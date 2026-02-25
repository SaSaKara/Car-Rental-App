# Car Rental Management System (Tkinter)

A desktop-based car rental management application developed using **Python** and **Tkinter**.

## Features
- Add, edit, delete vehicle records
- Rent / return vehicles using a date range
- Filter and sort vehicle list
- Daily logs and revenue analytics
- JSON-based persistence (`vehicles.json`, `records.json`, `stats.json`)

## Tech Stack
- Python
- Tkinter
- tkcalendar
- JSON

## Project Structure
- `src/` UI + business logic + storage
- `data/` persistent JSON files
- `tests/` unit tests (pytest)

## How to Run
```bash
pip install -r requirements.txt
python src/app.py