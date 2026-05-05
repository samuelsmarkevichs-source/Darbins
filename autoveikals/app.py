from flask import Flask, render_template
import sqlite3
from pathlib import Path
app = Flask(__name__)


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
        
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")

@app.route("/par-mums")
def about():
    return render_template("about.html")

def get_db_connection():
    db = Path(__file__).parent / "miniveikals"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    return conn

# products = [
# {"id": 1, "name": "Zīmulis", "price": 0.50, "image": "pencil.jpg"},
# {"id": 2, "name": "Pildspalva", "price": 1.20, "image": "pen.jpg"},
# {"id": 3, "name": "Burtnīca", "price": 0.90, "image": "notebook.jpg"},
# {"id": 4, "name": "Mape", "price": 1.50, "image": "folder.jpg"},
# ]

if __name__ == "__main__":
    app.run(debug=True)
