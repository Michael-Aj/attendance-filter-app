# Attendance Filter App

Flask web app for lecturers to upload a weekly attendance CSV and instantly
download a new file containing only **absent** records.

## Quick Start (local)

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py                  # browse to http://127.0.0.1:5000
