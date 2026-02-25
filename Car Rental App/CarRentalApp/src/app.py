import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry

from src.storage import JsonStorage
from src.service import CarRentalService


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Car Rental App")
        self.geometry("920x450")
        self.minsize(920, 450)
        self.config(padx=10, pady=10)

        self.storage = JsonStorage(data_dir="data")
        self.service = CarRentalService(self.storage)

        self._filter_after_id = None

        self._build_layout()
        self._build_left_panel()
        self._build_right_panel()

        self.refresh_vehicle_list()
        self.show_add_form()

    # ----------------------------
    # Layout
    # ----------------------------
    def _build_layout(self):
        self.canvas = tk.Canvas(self)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.content = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.content, anchor="nw")

        self.content.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.canvas.bind_all("<MouseWheel>", on_mousewheel)

        self.left_frame = tk.Frame(self.content)
        self.right_frame = tk.Frame(self.content)

        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        self.right_frame.grid(row=0, column=1, sticky="nsew")

        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_columnconfigure(1, weight=1)

        self.left_frame.grid_columnconfigure(0, weight=1)
        self.left_frame.grid_rowconfigure(1, weight=1)

        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_columnconfigure(1, weight=1)

    # ----------------------------
    # Left Panel (Tree + Filters)
    # ----------------------------
    def _build_left_panel(self):
        self.filter_var = tk.StringVar()
        self.status_var = tk.StringVar(value="All")

        self.filter_entry = tk.Entry(self.left_frame, textvariable=self.filter_var, width=30)
        self.filter_entry.grid(row=0, column=0, columnspan=2, sticky="w", pady=5)

        self.status_menu = tk.OptionMenu(self.left_frame, self.status_var, "All", "Available", "Rented")
        self.status_menu.grid(row=0, column=2, sticky="w", pady=5)

        self.tree = ttk.Treeview(
            self.left_frame,
            columns=("model", "plate", "price", "status"),
            show="headings",
            height=15
        )
        self.tree.grid(row=1, column=0, columnspan=4, sticky="nsew", pady=5)

        self.tree.heading("model", text="MODEL")
        self.tree.heading("plate", text="PLATE")
        self.tree.heading("price", text="PRICE/DAY")
        self.tree.heading("status", text="STATUS")

        self.tree.column("model", width=180, anchor="w")
        self.tree.column("plate", width=120, anchor="center")
        self.tree.column("price", width=90, anchor="center")
        self.tree.column("status", width=100, anchor="center")

        # Debounced refresh for better performance
        self.filter_var.trace_add("write", lambda *_: self.schedule_refresh())
        self.status_var.trace_add("write", lambda *_: self.refresh_vehicle_list())

        # Selection -> auto-fill plate fields in forms
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def schedule_refresh(self):
        if self._filter_after_id is not None:
            self.after_cancel(self._filter_after_id)
        self._filter_after_id = self.after(250, self.refresh_vehicle_list)

    def on_tree_select(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        if len(values) < 2:
            return
        plate = values[1]

        # Auto-fill any plate fields if visible
        self.ent_rent_plate.delete(0, tk.END)
        self.ent_rent_plate.insert(0, plate)

        self.ent_return_plate.delete(0, tk.END)
        self.ent_return_plate.insert(0, plate)

        self.ent_delete_plate.delete(0, tk.END)
        self.ent_delete_plate.insert(0, plate)

        self.ent_edit_old_plate.delete(0, tk.END)
        self.ent_edit_old_plate.insert(0, plate)

    def refresh_vehicle_list(self):
        for item in self.tree.get_children(""):
            self.tree.delete(item)

        text_filter = self.filter_var.get().strip().lower()
        status_filter = self.status_var.get()

        vehicles = self.service.list_vehicles()
        for v in vehicles:
            status_text = "Available" if v.status == "AVAILABLE" else "Rented"

            if status_filter != "All" and status_text != status_filter:
                continue

            if text_filter:
                if text_filter not in v.model_name.lower() and text_filter not in v.plate.lower():
                    continue

            self.tree.insert("", "end", values=(v.model_name, v.plate, f"{v.daily_price}", status_text))

    # ----------------------------
    # Right Panel (Forms)
    # ----------------------------
    def _build_right_panel(self):
        self.options_list = [
            "Add Vehicle",
            "Rent Vehicle",
            "Return Vehicle",
            "Edit Vehicle",
            "Delete Vehicle",
            "Daily Logs",
            "Report & Analytics"
        ]

        self.selected_option = tk.StringVar(self)
        self.selected_option.set(self.options_list[0])
        self.dropdown = tk.OptionMenu(self.right_frame, self.selected_option, *self.options_list)
        self.dropdown.grid(row=0, column=0, columnspan=2, pady=10, sticky="ew", padx=5)
        self.selected_option.trace_add("write", lambda *_: self.handle_action(self.selected_option.get()))

        # --- Add form widgets
        self.lbl_add_header = tk.Label(self.right_frame, text="ADD NEW VEHICLE", font=("Arial", 11, "bold"))
        self.lbl_add_model = tk.Label(self.right_frame, text="Model Name (e.g., Renault Clio):", anchor="w")
        self.ent_add_model = tk.Entry(self.right_frame, width=30)
        self.lbl_add_plate = tk.Label(self.right_frame, text="License Plate (e.g., 34 ABC 456):", anchor="w")
        self.ent_add_plate = tk.Entry(self.right_frame, width=30)
        self.lbl_add_price = tk.Label(self.right_frame, text="Daily Price (₺):", anchor="w")
        self.ent_add_price = tk.Entry(self.right_frame, width=30)
        self.btn_add_vehicle = tk.Button(self.right_frame, text="Add Vehicle", bg="green", fg="white", command=self.add_vehicle)

        # --- Rent form widgets
        self.lbl_rent_header = tk.Label(self.right_frame, text="VEHICLE RENTAL FORM", font=("Arial", 11, "bold"))
        self.lbl_rent_plate = tk.Label(self.right_frame, text="License Plate:", anchor="w")
        self.ent_rent_plate = tk.Entry(self.right_frame, width=30)
        self.lbl_rent_start = tk.Label(self.right_frame, text="Start Date:", anchor="w")
        self.ent_rent_start = DateEntry(self.right_frame, width=27, date_pattern="dd/mm/yyyy")
        self.lbl_rent_end = tk.Label(self.right_frame, text="End Date:", anchor="w")
        self.ent_rent_end = DateEntry(self.right_frame, width=27, date_pattern="dd/mm/yyyy")
        self.btn_rent_vehicle = tk.Button(self.right_frame, text="Rent Vehicle", bg="green", fg="white", command=self.rent_vehicle)

        # --- Return form widgets
        self.lbl_return_header = tk.Label(self.right_frame, text="VEHICLE RETURN FORM", font=("Arial", 11, "bold"))
        self.lbl_return_plate = tk.Label(self.right_frame, text="License Plate:", anchor="w")
        self.ent_return_plate = tk.Entry(self.right_frame, width=30)
        self.btn_return_vehicle = tk.Button(self.right_frame, text="Return Vehicle", bg="green", fg="white", command=self.return_vehicle)

        # --- Edit form widgets
        self.lbl_edit_header = tk.Label(self.right_frame, text="EDIT VEHICLE", font=("Arial", 11, "bold"))
        self.lbl_edit_old_plate = tk.Label(self.right_frame, text="Current Plate:", anchor="w")
        self.ent_edit_old_plate = tk.Entry(self.right_frame, width=30)
        self.lbl_edit_new_model = tk.Label(self.right_frame, text="New Model:", anchor="w")
        self.ent_edit_new_model = tk.Entry(self.right_frame, width=30)
        self.lbl_edit_new_plate = tk.Label(self.right_frame, text="New Plate:", anchor="w")
        self.ent_edit_new_plate = tk.Entry(self.right_frame, width=30)
        self.lbl_edit_new_price = tk.Label(self.right_frame, text="New Daily Price:", anchor="w")
        self.ent_edit_new_price = tk.Entry(self.right_frame, width=30)
        self.btn_edit_vehicle = tk.Button(self.right_frame, text="Update Vehicle", bg="green", fg="white", command=self.edit_vehicle)

        # --- Delete form widgets
        self.lbl_delete_header = tk.Label(self.right_frame, text="DELETE VEHICLE", font=("Arial", 11, "bold"))
        self.lbl_delete_plate = tk.Label(self.right_frame, text="License Plate:", anchor="w")
        self.ent_delete_plate = tk.Entry(self.right_frame, width=30)
        self.btn_delete_vehicle = tk.Button(self.right_frame, text="Delete Vehicle", bg="green", fg="white", command=self.delete_vehicle)

        # --- Logs / report widgets
        self.lbl_logs_header = tk.Label(self.right_frame, text="DAILY LOGS", font=("Arial", 11, "bold"))
        self.lbl_report_header = tk.Label(self.right_frame, text="REPORT & ANALYTICS", font=("Arial", 11, "bold"))
        self.lbl_report = tk.Label(self.right_frame, text="")
        self.lbl_available_header = tk.Label(self.right_frame, text="Available Vehicles:", font=("Arial", 9, "bold"))
        self.lbl_available = tk.Label(self.right_frame, text="")
        self.lbl_total_available = tk.Label(self.right_frame, text="")

    def clear_right_panel(self):
        for w in self.right_frame.grid_slaves():
            if w is self.dropdown:
                continue
            w.grid_forget()

    # ----------------------------
    # Actions
    # ----------------------------
    def add_vehicle(self):
        try:
            model = self.ent_add_model.get().strip()
            plate = self.ent_add_plate.get().strip()
            price = int(self.ent_add_price.get().strip())
            self.service.add_vehicle(model, plate, price)

            self.ent_add_model.delete(0, tk.END)
            self.ent_add_plate.delete(0, tk.END)
            self.ent_add_price.delete(0, tk.END)

            self.refresh_vehicle_list()
            messagebox.showinfo("Success", "Vehicle added successfully.")
        except Exception as e:
            messagebox.showwarning("Error", str(e))

    def rent_vehicle(self):
        try:
            plate = self.ent_rent_plate.get().strip()
            start = self.ent_rent_start.get_date()
            end = self.ent_rent_end.get_date()
            days, fee, model = self.service.rent_vehicle(plate, start, end)

            self.refresh_vehicle_list()
            messagebox.showinfo(
                "Success",
                f"Vehicle rented successfully.\nModel: {model}\nPlate: {plate}\nDays: {days}\nTotal Fee: {fee}₺"
            )
        except Exception as e:
            messagebox.showwarning("Error", str(e))

    def return_vehicle(self):
        try:
            plate = self.ent_return_plate.get().strip()
            model = self.service.return_vehicle(plate)
            self.refresh_vehicle_list()
            messagebox.showinfo("Success", f"Vehicle returned: {model} ({plate})")
        except Exception as e:
            messagebox.showwarning("Error", str(e))

    def edit_vehicle(self):
        try:
            old_plate = self.ent_edit_old_plate.get().strip()
            new_model = self.ent_edit_new_model.get().strip()
            new_plate = self.ent_edit_new_plate.get().strip()
            new_price = int(self.ent_edit_new_price.get().strip())
            self.service.edit_vehicle(old_plate, new_model, new_plate, new_price)

            self.refresh_vehicle_list()
            messagebox.showinfo("Success", "Vehicle updated successfully.")
        except Exception as e:
            messagebox.showwarning("Error", str(e))

    def delete_vehicle(self):
        try:
            plate = self.ent_delete_plate.get().strip()
            model = self.service.delete_vehicle(plate)
            self.refresh_vehicle_list()
            messagebox.showinfo("Success", f"Vehicle deleted: {model} ({plate})")
        except Exception as e:
            messagebox.showwarning("Error", str(e))

    # ----------------------------
    # Form Screens
    # ----------------------------
    def show_add_form(self):
        self.clear_right_panel()
        r = 1
        self.lbl_add_header.grid(row=r, column=0, columnspan=2, pady=(4, 6), sticky="ew"); r += 1
        self.lbl_add_model.grid(row=r, column=0, sticky="w")
        self.ent_add_model.grid(row=r, column=1, sticky="w", padx=5); r += 1
        self.lbl_add_plate.grid(row=r, column=0, sticky="w")
        self.ent_add_plate.grid(row=r, column=1, sticky="w", padx=5); r += 1
        self.lbl_add_price.grid(row=r, column=0, sticky="w")
        self.ent_add_price.grid(row=r, column=1, sticky="w", padx=5); r += 1
        self.btn_add_vehicle.grid(row=r, column=0, columnspan=2, pady=10, sticky="ew")

    def show_rent_form(self):
        self.clear_right_panel()
        r = 1
        self.lbl_rent_header.grid(row=r, column=0, columnspan=2, pady=(4, 6), sticky="ew"); r += 1
        self.lbl_rent_plate.grid(row=r, column=0, sticky="w")
        self.ent_rent_plate.grid(row=r, column=1, sticky="w", padx=5); r += 1
        self.lbl_rent_start.grid(row=r, column=0, sticky="w")
        self.ent_rent_start.grid(row=r, column=1, sticky="w", padx=5); r += 1
        self.lbl_rent_end.grid(row=r, column=0, sticky="w")
        self.ent_rent_end.grid(row=r, column=1, sticky="w", padx=5); r += 1
        self.btn_rent_vehicle.grid(row=r, column=0, columnspan=2, pady=10, sticky="ew")

    def show_return_form(self):
        self.clear_right_panel()
        r = 1
        self.lbl_return_header.grid(row=r, column=0, columnspan=2, pady=(4, 6), sticky="ew"); r += 1
        self.lbl_return_plate.grid(row=r, column=0, sticky="w")
        self.ent_return_plate.grid(row=r, column=1, sticky="w", padx=5); r += 1
        self.btn_return_vehicle.grid(row=r, column=0, columnspan=2, pady=10, sticky="ew")

    def show_edit_form(self):
        self.clear_right_panel()
        r = 1
        self.lbl_edit_header.grid(row=r, column=0, columnspan=2, pady=(4, 6), sticky="ew"); r += 1
        self.lbl_edit_old_plate.grid(row=r, column=0, sticky="w")
        self.ent_edit_old_plate.grid(row=r, column=1, sticky="w", padx=5); r += 1
        self.lbl_edit_new_model.grid(row=r, column=0, sticky="w", pady=(10, 0))
        self.ent_edit_new_model.grid(row=r, column=1, sticky="w", padx=5, pady=(10, 0)); r += 1
        self.lbl_edit_new_plate.grid(row=r, column=0, sticky="w")
        self.ent_edit_new_plate.grid(row=r, column=1, sticky="w", padx=5); r += 1
        self.lbl_edit_new_price.grid(row=r, column=0, sticky="w")
        self.ent_edit_new_price.grid(row=r, column=1, sticky="w", padx=5); r += 1
        self.btn_edit_vehicle.grid(row=r, column=0, columnspan=2, pady=10, sticky="ew")

    def show_delete_form(self):
        self.clear_right_panel()
        r = 1
        self.lbl_delete_header.grid(row=r, column=0, columnspan=2, pady=(4, 6), sticky="ew"); r += 1
        self.lbl_delete_plate.grid(row=r, column=0, sticky="w")
        self.ent_delete_plate.grid(row=r, column=1, sticky="w", padx=5); r += 1
        self.btn_delete_vehicle.grid(row=r, column=0, columnspan=2, pady=10, sticky="ew")

    def show_logs(self):
        self.clear_right_panel()
        self.lbl_logs_header.grid(row=1, column=0, columnspan=2, pady=(4, 6), sticky="ew")

        logs = self.service.get_recent_logs(limit=20)
        for i, line in enumerate(logs):
            tk.Label(self.right_frame, text=line, wraplength=650).grid(
                row=i + 2, column=0, columnspan=2, pady=2, sticky="w"
            )

    def show_report(self):
        self.clear_right_panel()
        self.lbl_report_header.grid(row=1, column=0, columnspan=2, pady=(4, 6), sticky="ew")

        total_revenue, available, available_count = self.service.get_report()

        self.lbl_report.config(text=f"Total Revenue: {total_revenue}₺")
        self.lbl_report.grid(row=2, column=0, columnspan=2, pady=10, sticky="w")

        self.lbl_available_header.grid(row=3, column=0, sticky="w")
        self.lbl_available.config(text="\n".join([f"{v.model_name} - {v.plate} - {v.daily_price}₺/day" for v in available]))
        self.lbl_available.grid(row=4, column=0, columnspan=2, sticky="w")

        self.lbl_total_available.config(text=f"\nTotal Available Vehicles: {available_count}")
        self.lbl_total_available.grid(row=5, column=0, sticky="w")

    def handle_action(self, selection: str):
        width, height = 920, 450

        if selection == "Add Vehicle":
            self.show_add_form()
        elif selection == "Rent Vehicle":
            self.show_rent_form()
        elif selection == "Return Vehicle":
            self.show_return_form()
        elif selection == "Edit Vehicle":
            self.show_edit_form()
        elif selection == "Delete Vehicle":
            self.show_delete_form()
        elif selection == "Daily Logs":
            self.show_logs()
            width = 1200
        elif selection == "Report & Analytics":
            self.show_report()

        self.geometry(f"{width}x{height}")


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()