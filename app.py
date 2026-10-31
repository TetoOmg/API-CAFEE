import json
import os
import sqlite3
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)

# Orígenes permitidos. Cuando tengas tu usuario de GitHub, cambia "*" por:
# ["https://TU-USUARIO.github.io"]
CORS(app, origins=os.environ.get("ALLOWED_ORIGINS", "*").split(","))

DB = os.environ.get("DB_PATH", "cafeteria.db")


def log(msg):
    """Imprime una línea clara en los Logs de Render."""
    print(msg, flush=True)


def clean(s, limit=200):
    """Quita saltos de línea para que nadie falsifique líneas del log."""
    return str(s).replace("\n", " ").replace("\r", " ")[:limit]


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with db() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS ratings(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER, product TEXT, stars INTEGER, created TEXT);
            CREATE TABLE IF NOT EXISTS comments(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, text TEXT, date TEXT, created TEXT);
            CREATE TABLE IF NOT EXISTS orders(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                items TEXT, total REAL, created TEXT);
            """
        )


init_db()


def now():
    return datetime.now(timezone.utc).isoformat()


@app.get("/")
def health():
    return jsonify(status="ok", service="cafeteria")


@app.post("/ratings")
def add_rating():
    d = request.get_json(silent=True) or {}
    stars = d.get("stars")
    if not isinstance(stars, int) or not 1 <= stars <= 5:
        return jsonify(error="stars debe ser un entero de 1 a 5"), 400
    product = str(d.get("product", ""))[:100]
    with db() as con:
        con.execute(
            "INSERT INTO ratings(product_id, product, stars, created) VALUES(?,?,?,?)",
            (d.get("product_id"), product, stars, now()),
        )
    log(f"[ESTRELLAS] {stars}/5 para: {clean(product, 100)}")
    return jsonify(ok=True), 201


@app.get("/ratings")
def avg_ratings():
    with db() as con:
        rows = con.execute(
            "SELECT product_id, ROUND(AVG(stars),2) AS avg, COUNT(*) AS votes "
            "FROM ratings GROUP BY product_id"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.get("/comments")
def list_comments():
    with db() as con:
        rows = con.execute(
            "SELECT name, text, date FROM comments ORDER BY id DESC LIMIT 100"
        ).fetchall()
    return jsonify([dict(r) for r in reversed(rows)])


@app.post("/comments")
def add_comment():
    d = request.get_json(silent=True) or {}
    name = str(d.get("name", "")).strip()[:40]
    text = str(d.get("text", "")).strip()[:400]
    if not name or not text:
        return jsonify(error="name y text son obligatorios"), 400
    date = str(d.get("date", ""))[:20]
    with db() as con:
        con.execute(
            "INSERT INTO comments(name, text, date, created) VALUES(?,?,?,?)",
            (name, text, date, now()),
        )
    log(f"[COMENTARIO] {clean(name, 40)}: {clean(text, 400)}")
    return jsonify(ok=True), 201


@app.post("/orders")
def add_order():
    d = request.get_json(silent=True) or {}
    items = d.get("items")
    if not isinstance(items, list) or not items:
        return jsonify(error="items no puede estar vacío"), 400
    try:
        total = float(d.get("total", 0))
    except (TypeError, ValueError):
        return jsonify(error="total inválido"), 400
    with db() as con:
        cur = con.execute(
            "INSERT INTO orders(items, total, created) VALUES(?,?,?)",
            (json.dumps(items, ensure_ascii=False), total, now()),
        )
    detalle = ", ".join(
        f"{clean(i.get('qty', '?'), 5)}x {clean(i.get('name', '?'), 60)}"
        for i in items
        if isinstance(i, dict)
    )
    log(f"[PEDIDO #{cur.lastrowid}] {detalle} | Total: ${total:.0f}")
    return jsonify(ok=True, order_id=cur.lastrowid), 201


if __name__ == "__main__":
    app.run(debug=True)
