from flask import Flask, render_template, request, redirect, session, flash, make_response
from database import get_db, init_db
from datetime import datetime
import sqlite3
import re
import os

app = Flask(__name__)
app.secret_key = "SECRET_KEY"
init_db()

@app.route("/")
def index():
    if session.get("logged_in"):
        return redirect("/home")

    return redirect("/login")

#LOGIN----------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if username == "admin" and password == "0000":
            session["logged_in"] = True
            session["username"] = "admin"
            session["role"] = "Admin"
            return redirect("/home")
        else:
            flash("Wrong username or password", "danger")

    return render_template("login.html")

#HOME----------------------------------------------
@app.route("/home")
def home():
    if not session.get("logged_in"):
        return redirect("/login")

    now = datetime.now()
    conn = get_db()
    cursor = conn.cursor()

    try:
        total_beneficiaries = cursor.execute("SELECT COUNT(*) FROM beneficiaries").fetchone()[0]
        received = cursor.execute("SELECT COUNT(*) FROM dispenses WHERE dispense_month = ? AND dispense_year = ?", (now.month, now.year)).fetchone()[0]
        medicine = cursor.execute("SELECT SUM(stock_quantity) FROM medicines").fetchone()[0]

        low_stock = cursor.execute("""
            SELECT m.name, m.stock_quantity AS stock, COALESCE(SUM(bm.monthly_quantity), 0) AS needed
            FROM medicines m
            LEFT JOIN beneficiary_medicines bm ON m.id = bm.medicine_id
            GROUP BY m.id
            HAVING m.stock_quantity < COALESCE(SUM(bm.monthly_quantity), 0)
            ORDER BY m.stock_quantity ASC
        """).fetchall()

        return render_template("home.html", low_stock=low_stock, total_beneficiaries=total_beneficiaries, received=received, medicine=medicine)

    finally:
        conn.close()

#MEDICINE-------------------------------------------
@app.route("/admin/medicine", methods=["GET", "POST"])
def medicine():
    if not (session.get("logged_in") and session.get("role") == "Admin"):
        return redirect("/home")

    conn = get_db()
    cursor = conn.cursor()

    try:
        if request.method == "POST":
            action = request.form.get("action")

            if action == "add":
                name = request.form.get("name", "").strip().capitalize()
                stock_quantity = int(request.form.get("quantity", 0))
                try:
                    cursor.execute("INSERT INTO medicines (name, stock_quantity) VALUES (?, ?)", (name, stock_quantity))
                    conn.commit()
                    flash("Medicine added successfully", "success")
                except sqlite3.IntegrityError:
                    flash("The medicine was already exist", "danger")

            elif action == "save_all":
                medicine_ids = request.form.getlist("medicine_ids[]")
                stock_quantity = request.form.getlist("quantities[]")

                for med_id, qty in zip(medicine_ids, stock_quantity):
                    qty = qty.strip()
                    if not qty:
                        continue
                    try:
                        qty = int(qty)
                        if int(qty) < 1:
                            flash(f"Invalid quantity for medicine ID {med_id}. Skipping.", "warning")
                            continue

                        cursor.execute("UPDATE medicines SET stock_quantity = ? WHERE id = ?", (int(qty), med_id))
                    except ValueError:
                        flash(f"Invalid quantity for medicine ID {med_id}. Skipping.", "warning")
                        continue


                conn.commit()
                flash("Stock updated successfully", "success")

            elif action == "delete":
                medicine_id = request.form.get("medicine_id")
                in_use = cursor.execute("SELECT COUNT(*) FROM beneficiary_medicines WHERE medicine_id = ?", (medicine_id,)).fetchone()[0]

                if in_use > 0:
                    flash("Cannot delete: medicine is assigned to a beneficiary", "danger")
                else:
                    cursor.execute("DELETE FROM medicines WHERE id = ?", (medicine_id,))
                    conn.commit()
                    flash("Medicine deleted", "success")

            return redirect("/admin/medicine")

        cursor.execute("SELECT m.id, m.name, m.stock_quantity, COALESCE(SUM(bm.monthly_quantity), 0) AS needed FROM medicines m LEFT JOIN beneficiary_medicines bm ON m.id = bm.medicine_id GROUP BY m.id, m.name, m.stock_quantity")
        medicines = cursor.fetchall()

        return render_template("medicine.html", medicines=medicines)

    finally:
        conn.close()

#ADD-Beneficiaries-------------------------------------------
@app.route("/admin/add_beneficiary", methods=["GET", "POST"])
def add_beneficiary():
    if not (session.get("logged_in") and session.get("role") == "Admin"):
        return redirect("/home")

    if request.method == "POST":
        conn = get_db()
        cursor = conn.cursor()

        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        national_id = request.form.get("national_id", "").strip()

        governorate_codes = [
            "01", "02", "03", "04",
            "11", "12", "13", "14", "15", "16", "17", "18", "19",
            "21", "22", "23", "24", "25", "26", "27", "28", "29",
            "31", "32", "33", "34", "35", "88"
        ]

        if not re.match(r'^[a-zA-Z\u0600-\u06FF\s]{3,}$', name):
            conn.close()
            flash("Invalid name", "danger")
            return redirect("/admin/add_beneficiary")

        if not re.match(r'^01[0125][0-9]{8}$', phone):
            conn.close()
            flash("Invalid phone number", "danger")
            return redirect("/admin/add_beneficiary")

        if not re.match(r'^[23][0-9]{13}$', national_id) or national_id[7:9] not in governorate_codes:
            conn.close()
            flash("Invalid National ID", "danger")
            return redirect("/admin/add_beneficiary")

        try:
            cursor.execute("INSERT INTO beneficiaries (name, phone, national_id) VALUES (?, ?, ?)", (name, phone, national_id))
        except sqlite3.IntegrityError:
            conn.close()
            flash("This beneficiary already exists", "danger")
            return redirect("/admin/add_beneficiary")

        family_id = cursor.lastrowid

        selected_medicines = request.form.getlist("medicines[]")
        quantities = request.form.getlist("quantities[]")

        seen = []
        for med, qty in zip(selected_medicines, quantities):
            med = med.strip().capitalize()
            if med == "" or med in seen:
                continue
            seen.append(med)
            cursor.execute("SELECT id FROM medicines WHERE name = ?", (med,))
            row = cursor.fetchone()
            if row:
                cursor.execute("INSERT INTO beneficiary_medicines (beneficiary_id, medicine_id, monthly_quantity) VALUES (?, ?, ?)", (family_id, row["id"], int(qty)))

        conn.commit()
        flash("Beneficiary added successfully", "success")
        conn.close()
        return redirect("/admin/add_beneficiary")

    conn = get_db()
    cursor = conn.cursor()
    medicines = cursor.execute("SELECT * FROM medicines").fetchall()
    conn.close()

    return render_template("add_beneficiary.html", medicines=medicines)

#SHOW-Beneficiaries------------------------------------------
@app.route("/admin/beneficiaries", methods=["GET"])
def beneficiaries():
    if not (session.get("logged_in") and session.get("role") == "Admin"):
        return redirect("/home")

    now = datetime.now()
    conn = get_db()
    cursor = conn.cursor()

    try:
        beneficiaries = cursor.execute("""
            SELECT b.*,
                CASE WHEN EXISTS (
                    SELECT 1 FROM dispenses d
                    WHERE d.beneficiary_id = b.id
                    AND d.dispense_month = ?
                    AND d.dispense_year = ?
                ) THEN 1 ELSE 0 END AS received
            FROM beneficiaries b
        """, (now.month, now.year)).fetchall()

        return render_template("beneficiaries.html", beneficiaries=beneficiaries)
    finally:
        conn.close()

#COMPLETE-Beneficiaries--------------------------------------
@app.route("/admin/beneficiaries/complete_beneficiary/<int:beneficiary_id>", methods=["POST"])
def complete_beneficiary(beneficiary_id):
    if not (session.get("logged_in") and session.get("role") == "Admin"):
        return redirect("/home")

    now = datetime.now()
    conn = get_db()
    cursor = conn.cursor()

    try:
        already_received = cursor.execute("SELECT COUNT(*) FROM dispenses WHERE beneficiary_id = ? AND dispense_month = ? AND dispense_year = ?", (beneficiary_id, now.month, now.year)).fetchone()[0] > 0

        if already_received:
            flash("The family was already received", "warning")
        else:
            medicines_needed = cursor.execute("SELECT m.name, m.stock_quantity, bm.monthly_quantity, bm.medicine_id FROM beneficiary_medicines bm JOIN medicines m ON bm.medicine_id = m.id WHERE bm.beneficiary_id = ?", (beneficiary_id,)).fetchall()

            if not medicines_needed:
                flash("This family has no medicine", "warning")
            else:
                short = [m["name"] for m in medicines_needed if m["stock_quantity"] < m["monthly_quantity"]]

                if short:
                    flash(f"Small quantity of {', '.join(short)}", "danger")
                else:
                    for m in medicines_needed:
                        cursor.execute("UPDATE medicines SET stock_quantity = stock_quantity - ? WHERE name = ?", (m["monthly_quantity"], m["name"]))

                    cursor.execute("INSERT INTO dispenses (beneficiary_id, dispense_day, dispense_month, dispense_year) VALUES (?, ?, ?, ?)", (beneficiary_id, now.day, now.month, now.year))
                    dispense_id = cursor.lastrowid

                    for m in medicines_needed:
                        cursor.execute("INSERT INTO dispense_items (dispense_id, medicine_id, quantity) VALUES (?, ?, ?)", (dispense_id, m["medicine_id"], m["monthly_quantity"]))

                    conn.commit()
                    flash("Received", "success")
    finally:
        conn.close()

    return redirect("/admin/beneficiaries")

#VIEW-Beneficiaries------------------------------------------
@app.route("/admin/beneficiaries/view_beneficiary/<int:beneficiary_id>", methods=["GET"])
def view_beneficiary(beneficiary_id):
    if not (session.get("logged_in") and session.get("role") == "Admin"):
        return redirect("/home")

    conn = get_db()
    cursor = conn.cursor()

    try:
        beneficiary = cursor.execute("SELECT * FROM beneficiaries WHERE id = ?", (beneficiary_id,)).fetchone()
        if beneficiary is None:
            return redirect("/home")

        medicines = cursor.execute("SELECT m.name, bm.monthly_quantity FROM beneficiary_medicines bm JOIN medicines m ON bm.medicine_id = m.id WHERE bm.beneficiary_id = ?", (beneficiary_id,)).fetchall()
        history = cursor.execute("""
            SELECT d.dispense_day, d.dispense_month, d.dispense_year, m.name, di.quantity
            FROM dispenses d
            JOIN dispense_items di ON di.dispense_id = d.id
            JOIN medicines m ON m.id = di.medicine_id
            WHERE beneficiary_id = ?
            ORDER BY d.dispense_year DESC, d.dispense_month DESC, d.dispense_day DESC
            """, (beneficiary_id,)).fetchall()

        grouped_history = {}
        for record in history:
            date = (record["dispense_day"], record["dispense_month"], record["dispense_year"])
            if date not in grouped_history:
                grouped_history[date] = []
            grouped_history[date].append({"name": record["name"], "quantity": record["quantity"]})

        return render_template("view_beneficiaries.html", beneficiary=beneficiary, medicines=medicines, history=grouped_history)
    finally:
        conn.close()

#DELETE-Beneficiaries------------------------------------------
@app.route("/admin/beneficiaries/delete_beneficiary/<int:beneficiary_id>", methods=["POST"])
def delete_beneficiary(beneficiary_id):
    if not (session.get("logged_in") and session.get("role") == "Admin"):
        return redirect("/home")

    conn = get_db()
    cursor = conn.cursor()

    try:
        dispense_ids = cursor.execute("SELECT id FROM dispenses WHERE beneficiary_id = ?", (beneficiary_id,)).fetchall()

        for d in dispense_ids:
            cursor.execute("DELETE FROM dispense_items WHERE dispense_id = ?", (d["id"],))

        cursor.execute("DELETE FROM dispenses WHERE beneficiary_id = ?", (beneficiary_id,))

        cursor.execute("DELETE FROM beneficiary_medicines WHERE beneficiary_id = ?", (beneficiary_id,))

        cursor.execute("DELETE FROM beneficiaries WHERE id = ?", (beneficiary_id,))

        conn.commit()
        flash("Beneficiary deleted", "success")
    finally:
        conn.close()

    return redirect("/admin/beneficiaries")


#LOGOUT----------------------------------------------
@app.route("/logout")
def logout():
    session.clear()

    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)
