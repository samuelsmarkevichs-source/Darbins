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


@app.route("/produkti/<int:product_id>")
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
    conn.close()
    return render_template("products_show.html", product=product)


@app.route("/crudelis", methods=["GET", "POST"])
def crudelis():
    conn = get_db_connection()
    manufacturers = conn.execute("SELECT * FROM manufacturers ORDER BY name").fetchall()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price = request.form.get("price", "").strip()
        manufacturer_id = request.form.get("manufacturer_id", "").strip()
        image_file = request.files.get("image")

        errors = []
        if not name:
            errors.append("Nosaukums ir obligāts.")
        if not price:
            errors.append("Cena ir obligāta.")
        else:
            try:
                price = float(price)
            except ValueError:
                errors.append("Cenai jābūt skaitlim.")

        image_filename = None
        if image_file and image_file.filename:
            if allowed_file(image_file.filename):
                from werkzeug.utils import secure_filename
                image_filename = secure_filename(image_file.filename)
                UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
                image_file.save(UPLOAD_FOLDER / image_filename)
            else:
                errors.append("Atļautie attēlu formāti: PNG, JPG, JPEG, WEBP, GIF.")

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
    return render_template("404.html")


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