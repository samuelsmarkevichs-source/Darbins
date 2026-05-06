from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path
import os

app = Flask(__name__)
app.secret_key = "automeistari-secret-key"

UPLOAD_FOLDER = Path(__file__).parent / "static" / "images" / "products"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/produkti")
def products():
    conn = get_db_connection()
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return render_template("products.html", products=products)


@app.route("/produkti/<int:product_id>", methods=["GET", "POST"])
def products_show(product_id):
    conn = get_db_connection()
    product = conn.execute(
        """
        SELECT products.*, manufacturers.name AS manufacturer
        FROM products
        LEFT JOIN manufacturers ON products.manufacturer_id = manufacturers.id
        WHERE products.id = ?
        """,
        (product_id,),
    ).fetchone()

    if product is None:
        conn.close()
        return render_template("404.html"), 404

    reviews = conn.execute(
        "SELECT * FROM reviews WHERE product_id = ? ORDER BY created_at DESC",
        (product_id,),
    ).fetchall()

    avg_rating = conn.execute(
        "SELECT ROUND(AVG(rating), 1) as avg FROM reviews WHERE product_id = ?",
        (product_id,),
    ).fetchone()["avg"]

    conn.close()
    return render_template(
        "products_show.html",
        product=product,
        reviews=reviews,
        avg_rating=avg_rating,
    )


@app.route("/produkti/<int:product_id>/review", methods=["POST"])
def add_review(product_id):
    author = request.form.get("author", "").strip()
    rating = request.form.get("rating", "").strip()
    body   = request.form.get("body", "").strip()

    errors = []
    if not author:
        errors.append("Vards ir obligats.")
    if not rating or not rating.isdigit() or int(rating) not in range(1, 6):
        errors.append("Izveleties vertejumu no 1 lidz 5.")
    if not body:
        errors.append("Komentars nevar but tukss.")

    if errors:
        flash("review_error|" + "|".join(errors))
    else:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO reviews (product_id, author, rating, body) VALUES (?, ?, ?, ?)",
            (product_id, author, int(rating), body),
        )
        conn.commit()
        conn.close()
        flash("review_ok")

    return redirect(url_for("products_show", product_id=product_id) + "#reviews")


@app.route("/produkti/<int:product_id>/inquiry", methods=["POST"])
def add_inquiry(product_id):
    name    = request.form.get("name", "").strip()
    email   = request.form.get("email", "").strip()
    phone   = request.form.get("phone", "").strip()
    message = request.form.get("message", "").strip()

    errors = []
    if not name:    errors.append("Vards ir obligats.")
    if not email:   errors.append("E-pasts ir obligats.")
    if not message: errors.append("Zinojums nevar but tukss.")

    if errors:
        flash("inquiry_error|" + "|".join(errors))
    else:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO inquiries (product_id, name, email, phone, message) VALUES (?, ?, ?, ?, ?)",
            (product_id, name, email, phone or None, message),
        )
        conn.commit()
        conn.close()
        flash("inquiry_ok")

    return redirect(url_for("products_show", product_id=product_id) + "#inquiry")


@app.route("/admin/pieprasijumi")
def admin_inquiries():
    conn = get_db_connection()
    inquiries = conn.execute(
        """
        SELECT inquiries.*, products.name AS product_name
        FROM inquiries
        LEFT JOIN products ON inquiries.product_id = products.id
        ORDER BY inquiries.created_at DESC
        """
    ).fetchall()
    conn.close()
    return render_template("admin_inquiries.html", inquiries=inquiries)


@app.route("/admin/pieprasijumi/<int:inquiry_id>/status", methods=["POST"])
def update_inquiry_status(inquiry_id):
    status = request.form.get("status")
    if status in ("jauns", "skatits", "atbildets"):
        conn = get_db_connection()
        conn.execute("UPDATE inquiries SET status = ? WHERE id = ?", (status, inquiry_id))
        conn.commit()
        conn.close()
    return redirect(url_for("admin_inquiries"))


@app.route("/crudelis", methods=["GET", "POST"])
def crudelis():
    conn = get_db_connection()
    manufacturers = conn.execute("SELECT * FROM manufacturers ORDER BY name").fetchall()

    if request.method == "POST":
        name            = request.form.get("name", "").strip()
        price           = request.form.get("price", "").strip()
        manufacturer_id = request.form.get("manufacturer_id", "").strip()
        image_file      = request.files.get("image")

        errors = []
        if not name:
            errors.append("Nosaukums ir obligats.")
        if not price:
            errors.append("Cena ir obligata.")
        else:
            try:
                price = float(price)
            except ValueError:
                errors.append("Cenai jabut skaitlim.")

        image_filename = None
        if image_file and image_file.filename:
            if allowed_file(image_file.filename):
                from werkzeug.utils import secure_filename
                image_filename = secure_filename(image_file.filename)
                UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
                image_file.save(UPLOAD_FOLDER / image_filename)
            else:
                errors.append("Atlautie attelu formati: PNG, JPG, JPEG, WEBP, GIF.")

        if errors:
            conn.close()
            return render_template("crudelis.html", errors=errors, manufacturers=manufacturers)

        conn.execute(
            "INSERT INTO products (name, price, image, manufacturer_id) VALUES (?, ?, ?, ?)",
            (name, price, image_filename, manufacturer_id if manufacturer_id else None),
        )
        conn.commit()
        conn.close()
        flash("success")
        return redirect(url_for("crudelis"))

    conn.close()
    return render_template("crudelis.html", manufacturers=manufacturers)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.route("/par-mums")
def about():
    return render_template("about.html")


def get_db_connection():
    db = Path(__file__).parent / "miniveikals.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    return conn


if __name__ == "__main__":
    app.run(debug=True)