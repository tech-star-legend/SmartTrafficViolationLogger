from __future__ import annotations

import io
import os
import uuid
from datetime import datetime

import qrcode
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_sqlalchemy import SQLAlchemy






BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "traffic_violations.sqlite3")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + DB_PATH
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy(app)


class Violation(db.Model):
    __tablename__ = "violations"

    id = db.Column(db.Integer, primary_key=True)
    challan_no = db.Column(db.String(64), unique=True, nullable=False, index=True)

    vehicle_no = db.Column(db.String(32), nullable=False, index=True)
    violation_type = db.Column(db.String(80), nullable=False)
    location = db.Column(db.String(120), nullable=False)

    # store as date for simpler filtering
    violation_date = db.Column(db.Date, nullable=False, index=True)

    fine_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(16), nullable=False, default="Unpaid", index=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<Violation challan_no={self.challan_no} vehicle_no={self.vehicle_no} "
            f"status={self.status}>"
        )


def _parse_date(value: str) -> datetime.date:
    value = value.strip()
    # expected format: YYYY-MM-DD (from HTML date input)
    return datetime.strptime(value, "%Y-%m-%d").date()


def _generate_challan_no() -> str:
    return uuid.uuid4().hex.upper()[:16]


def _qr_png_bytes_for_challan(challan_no: str) -> bytes:
    # Public status URL
    status_url = url_for("public_status", challan_no=challan_no, _external=True)

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(status_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    # qrcode's PIL-like image may be backed by a pure PNG writer (pypng),
    # so avoid passing a `format=` kwarg.
    img.save(buf)
    buf.seek(0)
    return buf.read()



@app.before_request
def _ensure_db():
    # Create tables on first run.
    db.create_all()


def _get_dashboard_stats():
    total = db.session.query(Violation.id).count()
    paid = db.session.query(Violation.id).filter(Violation.status == "Paid").count()
    unpaid = db.session.query(Violation.id).filter(Violation.status == "Unpaid").count()
    return total, paid, unpaid



@app.route("/")
def home():
    # Dashboard landing page
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    total, paid, unpaid = _get_dashboard_stats()
    return render_template(
        "dashboard.html",
        total=total,
        paid=paid,
        unpaid=unpaid,
    )



@app.route("/violations/new", methods=["GET", "POST"])
def add_violation():
    if request.method == "POST":
        vehicle_no = (request.form.get("vehicle_no") or "").strip().upper()
        violation_type = (request.form.get("violation_type") or "").strip()
        location = (request.form.get("location") or "").strip()
        violation_date_str = (request.form.get("violation_date") or "").strip()
        fine_amount_str = (request.form.get("fine_amount") or "").strip()

        if not vehicle_no:
            flash("Vehicle number is required.", "error")
        elif not violation_type:
            flash("Violation type is required.", "error")
        elif not location:
            flash("Location is required.", "error")
        elif not violation_date_str:
            flash("Date is required.", "error")
        elif not fine_amount_str:
            flash("Fine amount is required.", "error")
        else:
            try:
                violation_date = _parse_date(violation_date_str)
                fine_amount = float(fine_amount_str)
                challan_no = _generate_challan_no()

                v = Violation(
                    challan_no=challan_no,
                    vehicle_no=vehicle_no,
                    violation_type=violation_type,
                    location=location,
                    violation_date=violation_date,
                    fine_amount=fine_amount,
                    status="Unpaid",
                )
                db.session.add(v)
                db.session.commit()

                return redirect(url_for("challan", challan_no=challan_no))
            except ValueError:
                flash("Invalid date or fine amount.", "error")

    return render_template("add_violation.html")


@app.route("/challan/<challan_no>")
def challan(challan_no: str):
    violation = Violation.query.filter_by(challan_no=challan_no.upper()).first()
    if not violation:
        flash("Challan not found.", "error")
        return redirect(url_for("view_violations"))

    return render_template("challan.html", violation=violation)


@app.route("/qr/<challan_no>.png")
def qr(challan_no: str):
    violation = Violation.query.filter_by(challan_no=challan_no.upper()).first()
    if not violation:
        # Return 404 with empty body
        from flask import abort

        abort(404)

    png = _qr_png_bytes_for_challan(violation.challan_no)
    return app.response_class(png, mimetype="image/png")


@app.route("/public/status/<challan_no>")
def public_status(challan_no: str):
    violation = Violation.query.filter_by(challan_no=challan_no.upper()).first()
    if not violation:
        return render_template("public_status_not_found.html", challan_no=challan_no)

    return render_template("public_status.html", violation=violation)


@app.route("/violations", methods=["GET"])
def view_violations():
    vehicle_no = (request.args.get("vehicle_no") or "").strip().upper()
    status = (request.args.get("status") or "").strip()
    violation_type = (request.args.get("violation_type") or "").strip()

    date_from_str = (request.args.get("date_from") or "").strip()
    date_to_str = (request.args.get("date_to") or "").strip()

    query = Violation.query

    if vehicle_no:
        query = query.filter(Violation.vehicle_no == vehicle_no)

    if status:
        # allow Unpaid/Paid
        query = query.filter(Violation.status == status)

    if violation_type:
        query = query.filter(Violation.violation_type.ilike(f"%{violation_type}%"))

    if date_from_str:
        try:
            date_from = _parse_date(date_from_str)
            query = query.filter(Violation.violation_date >= date_from)
        except ValueError:
            flash("Invalid date_from format. Use YYYY-MM-DD.", "error")

    if date_to_str:
        try:
            date_to = _parse_date(date_to_str)
            query = query.filter(Violation.violation_date <= date_to)
        except ValueError:
            flash("Invalid date_to format. Use YYYY-MM-DD.", "error")

    violations = query.order_by(Violation.violation_date.desc(), Violation.id.desc()).all()

    return render_template(
        "view_violations.html",
        violations=violations,
        filters={
            "vehicle_no": vehicle_no,
            "status": status,
            "violation_type": violation_type,
            "date_from": date_from_str,
            "date_to": date_to_str,
        },
    )


@app.route("/violations/<challan_no>/update", methods=["POST"])
def update_violation(challan_no: str):
    violation = Violation.query.filter_by(challan_no=challan_no.upper()).first()
    if not violation:
        flash("Challan not found.", "error")
        return redirect(url_for("view_violations"))

    new_status = (request.form.get("status") or "").strip()
    if new_status not in ("Unpaid", "Paid"):
        flash("Invalid status.", "error")
        return redirect(url_for("challan", challan_no=violation.challan_no))

    violation.status = new_status
    db.session.commit()

    flash("Status updated.", "success")
    return redirect(url_for("challan", challan_no=violation.challan_no))


if __name__ == "__main__":
    # For local dev only
    app.run(debug=True, host="0.0.0.0", port=5000)

