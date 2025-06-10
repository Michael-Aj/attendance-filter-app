import pandas as pd
from flask import (
    Flask, render_template, request, redirect,
    url_for, send_file, flash
)
from io import BytesIO
import uuid
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-me")

download_cache = {}  # {token: bytes}


def filter_absent(df, attendance_col="Class Date"):
    df[attendance_col] = df[attendance_col].astype(str).str.strip().str.lower()
    return df[df[attendance_col] == "absent"].copy()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("csv_file")
        if not file or file.filename == "":
            flash("Please choose a CSV file.", "danger")
            return redirect(url_for("index"))

        try:
            df = pd.read_csv(file)
        except Exception as exc:
            flash(f"Could not read CSV: {exc}", "danger")
            return redirect(url_for("index"))

        attendance_col = next(
            (c for c in df.columns if c.lower() in ["class date", "attendance", "status"]),
            None
        )
        if attendance_col is None:
            flash("No attendance column found.", "warning")
            return redirect(url_for("index"))

        absent_df = filter_absent(df, attendance_col)

        # ── WRITE TO AN IN-MEMORY EXCEL FILE AND STORE RAW BYTES ─────────────
        b = BytesIO()
        with pd.ExcelWriter(b, engine="xlsxwriter") as writer:
            absent_df.to_excel(writer, index=False, sheet_name="Absent")
        xlsx_bytes = b.getvalue()            # pull the finished bytes
        # Cache the bytes with a unique token
        token = str(uuid.uuid4())
        download_cache[token] = xlsx_bytes
        # ─────────────────────────────────────────────────────────────────────

        return render_template(
            "result.html",
            tables=[absent_df.head(100).to_html(
                classes="table table-sm table-striped", index=False)],
            rows=len(absent_df),
            token=token
        )

    return render_template("index.html")


@app.route("/download/<token>")
def download(token):
    xlsx_bytes = download_cache.get(token)
    if xlsx_bytes is None:
        flash("Download expired or not found – please re-upload.", "warning")
        return redirect(url_for("index"))

    return send_file(
        BytesIO(xlsx_bytes),    # wrap bytes in a fresh buffer
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="absent_records.xlsx",
    )


if __name__ == "__main__":
    app.run(debug=True)
