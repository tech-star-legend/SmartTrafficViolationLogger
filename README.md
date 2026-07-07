# Smart Traffic Violation Logger (Flask)

Lightweight Flask app to add traffic violation records, view/filter history, generate a QR-based challan, and show public payment status.

## Features
- Add violation (auto-marked **Unpaid**)
- View/search violation history with filters
- Update status **Unpaid ↔ Paid**
- QR code on challan that opens a public status page
- SQLite + SQLAlchemy

## Setup (Windows)

### 1) Create virtual environment
```bat
python -m venv venv
```

### 2) Activate
```bat
venv\Scripts\activate
```

### 3) Install dependencies
```bat
pip install -r requirements.txt
```

### 4) Run
```bat
python app.py
```

Then open:
- App: http://localhost:5000

## How to use
1. Click **Add Violation**
2. Submit vehicle number, violation type, location, date, fine amount
3. You will be redirected to the **Challan** page with a QR code
4. Update **Unpaid/Paid** from the challan page
5. Scan QR to view the public status page

## Notes
- The QR code points to `/public/status/<challan_no>` on your running server.
- On first run, the SQLite DB file `traffic_violations.sqlite3` is created automatically.

