"""
app.py — On My Way Backend
Flask + MariaDB · Hackathon Blink Galaxy 2026
"""

import os
import math
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps

import pymysql
import pymysql.cursors
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, origins=os.getenv("CORS_ORIGINS", "*"))

app.config["SECRET_KEY"]   = os.getenv("SECRET_KEY",  "dev-secret")
app.config["JWT_SECRET"]   = os.getenv("JWT_SECRET",  "dev-jwt-secret")
app.config["JWT_EXPIRY_H"] = 24   # horas

# ═══════════════════════════════════════════════════════════════
#  BASE DE DATOS
# ═══════════════════════════════════════════════════════════════

def get_db():
    """Abre una conexión por request (se cierra automáticamente)."""
    if "db" not in g:
        g.db = pymysql.connect(
            host     = os.getenv("DB_HOST",     "localhost"),
            port     = int(os.getenv("DB_PORT", 3306)),
            user     = os.getenv("DB_USER",     "root"),
            password = os.getenv("DB_PASSWORD", ""),
            database = os.getenv("DB_NAME",     "onmyway_db"),
            cursorclass=pymysql.cursors.DictCursor,
            charset  = "utf8mb4",
        )
    return g.db

@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

# ═══════════════════════════════════════════════════════════════
#  JWT — UTILIDADES
# ═══════════════════════════════════════════════════════════════

def create_token(user_id: int, role: str) -> str:
    payload = {
        "sub":  user_id,
        "role": role,
        "iat":  datetime.now(timezone.utc),
        "exp":  datetime.now(timezone.utc) + timedelta(hours=app.config["JWT_EXPIRY_H"]),
    }
    return jwt.encode(payload, app.config["JWT_SECRET"], algorithm="HS256")

def decode_token(token: str) -> dict:
    return jwt.decode(token, app.config["JWT_SECRET"], algorithms=["HS256"])

def token_required(f):
    """Decorator: verifica JWT en el header Authorization."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token requerido"}), 401
        try:
            payload = decode_token(auth_header.split(" ")[1])
            g.user_id   = payload["sub"]
            g.user_role = payload["role"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido"}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """Decorator: además del JWT, verifica rol admin."""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if g.user_role != "admin":
            return jsonify({"error": "Acceso denegado"}), 403
        return f(*args, **kwargs)
    return decorated

# ═══════════════════════════════════════════════════════════════
#  HEALTH CHECK
# ═══════════════════════════════════════════════════════════════

@app.get("/api/health")
def health():
    try:
        db = get_db()
        with db.cursor() as cur:
            cur.execute("SELECT 1")
        return jsonify({"status": "ok", "db": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

# ═══════════════════════════════════════════════════════════════
#  AUTH — /api/auth
# ═══════════════════════════════════════════════════════════════

@app.post("/api/auth/register")
def register():
    data = request.get_json(silent=True) or {}
    name     = (data.get("name") or "").strip()
    email    = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "")

    if not name or not email or not password:
        return jsonify({"error": "Nombre, email y contraseña son requeridos"}), 400
    if len(password) < 8:
        return jsonify({"error": "La contraseña debe tener al menos 8 caracteres"}), 400

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                        (name, email, pw_hash))
        db.commit()
        with db.cursor() as cur:
            cur.execute("SELECT id, name, email, role FROM users WHERE email=%s", (email,))
            user = cur.fetchone()
        token = create_token(user["id"], user["role"])
        return jsonify({"token": token, "user": user}), 201
    except pymysql.IntegrityError:
        return jsonify({"error": "El email ya está registrado"}), 409

@app.post("/api/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    email    = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "")

    if not email or not password:
        return jsonify({"error": "Email y contraseña requeridos"}), 400

    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT id, name, email, role, password FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

    if not user or not bcrypt.checkpw(password.encode(), user["password"].encode()):
        return jsonify({"error": "Credenciales inválidas"}), 401

    user.pop("password")
    token = create_token(user["id"], user["role"])
    return jsonify({"token": token, "user": user}), 200

@app.get("/api/auth/me")
@token_required
def me():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT id, name, email, role, phone, created_at FROM users WHERE id=%s",
                    (g.user_id,))
        user = cur.fetchone()
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(user), 200

# ═══════════════════════════════════════════════════════════════
#  CATÁLOGO — /api/products  /api/categories
# ═══════════════════════════════════════════════════════════════

@app.get("/api/categories")
def get_categories():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT * FROM categories ORDER BY name")
        cats = cur.fetchall()
    return jsonify(cats), 200

@app.get("/api/products")
def get_products():
    search   = request.args.get("search",   "").strip()
    category = request.args.get("category", "")
    sort     = request.args.get("sort",     "created_at")
    order    = request.args.get("order",    "desc").upper()
    page     = max(1, int(request.args.get("page", 1)))
    per_page = min(50, int(request.args.get("per_page", 12)))

    allowed_sorts = {"price", "name", "created_at", "stock"}
    if sort not in allowed_sorts:
        sort = "created_at"
    if order not in ("ASC", "DESC"):
        order = "DESC"

    where_clauses = ["p.is_active = 1"]
    params = []

    if search:
        where_clauses.append("(p.name LIKE %s OR p.description LIKE %s)")
        params += [f"%{search}%", f"%{search}%"]
    if category:
        where_clauses.append("c.slug = %s")
        params.append(category)

    where = "WHERE " + " AND ".join(where_clauses)

    db = get_db()
    with db.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) AS total FROM products p JOIN categories c ON p.category_id=c.id {where}", params)
        total = cur.fetchone()["total"]

        offset = (page - 1) * per_page
        query = f"""
            SELECT p.*, c.name AS category_name, c.slug AS category_slug
            FROM products p
            JOIN categories c ON p.category_id = c.id
            {where}
            ORDER BY p.{sort} {order}
            LIMIT %s OFFSET %s
        """
        cur.execute(query, params + [per_page, offset])
        products = cur.fetchall()

    return jsonify({
        "data":        products,
        "total":       total,
        "page":        page,
        "per_page":    per_page,
        "total_pages": math.ceil(total / per_page),
    }), 200

@app.get("/api/products/<slug>")
def get_product(slug):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT p.*, c.name AS category_name, c.slug AS category_slug
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.slug = %s AND p.is_active = 1
        """, (slug,))
        product = cur.fetchone()
    if not product:
        return jsonify({"error": "Producto no encontrado"}), 404
    return jsonify(product), 200

# ═══════════════════════════════════════════════════════════════
#  CARRITO — /api/cart
# ═══════════════════════════════════════════════════════════════

def _get_or_create_cart(db, user_id: int) -> int:
    with db.cursor() as cur:
        cur.execute("SELECT id FROM carts WHERE user_id=%s", (user_id,))
        row = cur.fetchone()
        if row:
            return row["id"]
        cur.execute("INSERT INTO carts (user_id) VALUES (%s)", (user_id,))
        db.commit()
        return cur.lastrowid

@app.get("/api/cart")
@token_required
def get_cart():
    db = get_db()
    cart_id = _get_or_create_cart(db, g.user_id)
    with db.cursor() as cur:
        cur.execute("""
            SELECT ci.id, ci.quantity, ci.product_id,
                   p.name, p.price, p.image_url, p.stock, p.slug,
                   (ci.quantity * p.price) AS subtotal
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.id
            WHERE ci.cart_id = %s
        """, (cart_id,))
        items = cur.fetchall()
    total = sum(float(i["subtotal"]) for i in items)
    return jsonify({"items": items, "total": round(total, 2)}), 200

@app.post("/api/cart")
@token_required
def add_to_cart():
    data       = request.get_json(silent=True) or {}
    product_id = data.get("product_id")
    quantity   = max(1, int(data.get("quantity", 1)))

    if not product_id:
        return jsonify({"error": "product_id requerido"}), 400

    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT id, stock FROM products WHERE id=%s AND is_active=1", (product_id,))
        product = cur.fetchone()
    if not product:
        return jsonify({"error": "Producto no encontrado"}), 404
    if product["stock"] < quantity:
        return jsonify({"error": "Stock insuficiente"}), 400

    cart_id = _get_or_create_cart(db, g.user_id)
    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO cart_items (cart_id, product_id, quantity)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
        """, (cart_id, product_id, quantity))
    db.commit()
    return jsonify({"message": "Producto agregado al carrito"}), 201

@app.delete("/api/cart/<int:item_id>")
@token_required
def remove_from_cart(item_id):
    db = get_db()
    cart_id = _get_or_create_cart(db, g.user_id)
    with db.cursor() as cur:
        deleted = cur.execute(
            "DELETE FROM cart_items WHERE id=%s AND cart_id=%s", (item_id, cart_id)
        )
    db.commit()
    if deleted == 0:
        return jsonify({"error": "Item no encontrado"}), 404
    return jsonify({"message": "Item eliminado"}), 200

@app.delete("/api/cart")
@token_required
def clear_cart():
    db = get_db()
    cart_id = _get_or_create_cart(db, g.user_id)
    with db.cursor() as cur:
        cur.execute("DELETE FROM cart_items WHERE cart_id=%s", (cart_id,))
    db.commit()
    return jsonify({"message": "Carrito vaciado"}), 200

# ═══════════════════════════════════════════════════════════════
#  ENVÍOS — /api/shipping
# ═══════════════════════════════════════════════════════════════

@app.get("/api/shipping")
def get_shipping_methods():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT * FROM shipping_methods WHERE is_active=1")
        methods = cur.fetchall()
    return jsonify(methods), 200

# ═══════════════════════════════════════════════════════════════
#  ÓRDENES — /api/orders
# ═══════════════════════════════════════════════════════════════

@app.post("/api/orders")
@token_required
def create_order():
    data = request.get_json(silent=True) or {}
    shipping_method_id = data.get("shipping_method_id")
    shipping_name      = (data.get("shipping_name") or "").strip()
    shipping_address   = (data.get("shipping_address") or "").strip()
    shipping_city      = (data.get("shipping_city") or "").strip()
    shipping_zip       = (data.get("shipping_zip") or "").strip()
    shipping_phone     = (data.get("shipping_phone") or "").strip()
    notes              = (data.get("notes") or "").strip()

    if not all([shipping_method_id, shipping_name, shipping_address, shipping_city]):
        return jsonify({"error": "Datos de envío incompletos"}), 400

    db = get_db()
    cart_id = _get_or_create_cart(db, g.user_id)

    with db.cursor() as cur:
        cur.execute("""
            SELECT ci.quantity, p.price, p.stock, p.id AS product_id, p.name
            FROM cart_items ci JOIN products p ON ci.product_id=p.id
            WHERE ci.cart_id=%s
        """, (cart_id,))
        items = cur.fetchall()

    if not items:
        return jsonify({"error": "El carrito está vacío"}), 400

    # Verificar stock
    for item in items:
        if item["stock"] < item["quantity"]:
            return jsonify({"error": f"Stock insuficiente para {item['name']}"}), 400

    with db.cursor() as cur:
        cur.execute("SELECT price FROM shipping_methods WHERE id=%s AND is_active=1",
                    (shipping_method_id,))
        shipping = cur.fetchone()
    if not shipping:
        return jsonify({"error": "Método de envío inválido"}), 400

    subtotal      = sum(float(i["price"]) * i["quantity"] for i in items)
    shipping_cost = float(shipping["price"])
    total         = subtotal + shipping_cost

    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO orders
              (user_id, shipping_method_id, shipping_name, shipping_address,
               shipping_city, shipping_zip, shipping_phone, subtotal, shipping_cost, total, notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (g.user_id, shipping_method_id, shipping_name, shipping_address,
              shipping_city, shipping_zip, shipping_phone,
              subtotal, shipping_cost, total, notes))
        order_id = cur.lastrowid

        for item in items:
            line_subtotal = float(item["price"]) * item["quantity"]
            cur.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
                VALUES (%s,%s,%s,%s,%s)
            """, (order_id, item["product_id"], item["quantity"],
                  item["price"], line_subtotal))
            # Descontar stock
            cur.execute("UPDATE products SET stock=stock-%s WHERE id=%s",
                        (item["quantity"], item["product_id"]))

        # Vaciar carrito
        cur.execute("DELETE FROM cart_items WHERE cart_id=%s", (cart_id,))
    db.commit()

    return jsonify({"message": "Orden creada exitosamente", "order_id": order_id}), 201

@app.get("/api/orders")
@token_required
def get_user_orders():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT o.*, sm.name AS shipping_method_name
            FROM orders o
            JOIN shipping_methods sm ON o.shipping_method_id=sm.id
            WHERE o.user_id=%s ORDER BY o.created_at DESC
        """, (g.user_id,))
        orders = cur.fetchall()
    return jsonify(orders), 200

@app.get("/api/orders/<int:order_id>")
@token_required
def get_order(order_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT o.*, sm.name AS shipping_method_name
            FROM orders o
            JOIN shipping_methods sm ON o.shipping_method_id=sm.id
            WHERE o.id=%s AND o.user_id=%s
        """, (order_id, g.user_id))
        order = cur.fetchone()
    if not order:
        return jsonify({"error": "Orden no encontrada"}), 404

    with db.cursor() as cur:
        cur.execute("""
            SELECT oi.*, p.name, p.image_url, p.slug
            FROM order_items oi JOIN products p ON oi.product_id=p.id
            WHERE oi.order_id=%s
        """, (order_id,))
        order["items"] = cur.fetchall()

    return jsonify(order), 200

# ═══════════════════════════════════════════════════════════════
#  ADMIN — /api/admin  (requiere rol admin)
# ═══════════════════════════════════════════════════════════════

@app.get("/api/admin/orders")
@admin_required
def admin_orders():
    status = request.args.get("status", "")
    db = get_db()
    with db.cursor() as cur:
        if status:
            cur.execute("""
                SELECT o.*, u.name AS user_name, u.email, sm.name AS shipping_method_name
                FROM orders o JOIN users u ON o.user_id=u.id
                JOIN shipping_methods sm ON o.shipping_method_id=sm.id
                WHERE o.status=%s ORDER BY o.created_at DESC
            """, (status,))
        else:
            cur.execute("""
                SELECT o.*, u.name AS user_name, u.email, sm.name AS shipping_method_name
                FROM orders o JOIN users u ON o.user_id=u.id
                JOIN shipping_methods sm ON o.shipping_method_id=sm.id
                ORDER BY o.created_at DESC
            """)
        orders = cur.fetchall()
    return jsonify(orders), 200

@app.patch("/api/admin/orders/<int:order_id>/status")
@admin_required
def admin_update_order_status(order_id):
    data   = request.get_json(silent=True) or {}
    status = data.get("status")
    valid  = {"pending","processing","shipped","delivered","cancelled"}
    if status not in valid:
        return jsonify({"error": f"Status inválido. Opciones: {valid}"}), 400

    db = get_db()
    with db.cursor() as cur:
        cur.execute("UPDATE orders SET status=%s WHERE id=%s", (status, order_id))
    db.commit()
    return jsonify({"message": "Status actualizado"}), 200

@app.post("/api/admin/products")
@admin_required
def admin_create_product():
    data = request.get_json(silent=True) or {}
    required = ["category_id","name","slug","price","stock"]
    if not all(data.get(k) is not None for k in required):
        return jsonify({"error": f"Campos requeridos: {required}"}), 400

    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO products (category_id,name,slug,description,price,stock,image_url)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (data["category_id"], data["name"], data["slug"],
              data.get("description",""), data["price"], data["stock"],
              data.get("image_url","")))
        product_id = cur.lastrowid
    db.commit()
    return jsonify({"message": "Producto creado", "id": product_id}), 201

@app.put("/api/admin/products/<int:product_id>")
@admin_required
def admin_update_product(product_id):
    data = request.get_json(silent=True) or {}
    fields = {k: data[k] for k in
              ["name","slug","description","price","stock","image_url","is_active","category_id"]
              if k in data}
    if not fields:
        return jsonify({"error": "Sin campos para actualizar"}), 400

    set_clause = ", ".join(f"{k}=%s" for k in fields)
    db = get_db()
    with db.cursor() as cur:
        cur.execute(f"UPDATE products SET {set_clause} WHERE id=%s",
                    list(fields.values()) + [product_id])
    db.commit()
    return jsonify({"message": "Producto actualizado"}), 200

@app.delete("/api/admin/products/<int:product_id>")
@admin_required
def admin_delete_product(product_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("UPDATE products SET is_active=0 WHERE id=%s", (product_id,))
    db.commit()
    return jsonify({"message": "Producto desactivado"}), 200

# ═══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # host="0.0.0.0" es CRÍTICO para que sea accesible en red local (RasPi)
    app.run(host="0.0.0.0", port=5000, debug=(os.getenv("FLASK_ENV") == "development"))
