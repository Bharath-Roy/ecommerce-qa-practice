"""Small online shop used for QA practice.

python3 app/shop.py                    build 1.0 (has known defects)
SHOP_BUILD=1.1 python3 app/shop.py     build 1.1 (defects fixed)

Listens on 127.0.0.1 only. Data is in .data/shop.db, delete it to start over.
"""
import hashlib
import json
import os
import re
import secrets
import sqlite3
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

BUILD = os.environ.get("SHOP_BUILD", "1.0")
if BUILD not in ("1.0", "1.1"):
    raise SystemExit("SHOP_BUILD must be 1.0 or 1.1")
FIXED = BUILD == "1.1"

HERE = Path(__file__).resolve().parent
DB_PATH = os.environ.get("SHOP_DB") or str(HERE.parent / ".data" / "shop.db")
PORT = int(os.environ.get("PORT", "5060"))

FREE_SHIPPING_FROM = 50000      # paise, 500.00
SHIPPING_FEE = 4900             # 49.00
COUPON_CODE = "WELCOME10"
COUPON_MIN = 100000             # 1000.00
COUPON_CAP = 15000              # 150.00
COD_LIMIT = 5000000             # 50000.00
MAX_QTY = 10
CATEGORIES = ("Fashion", "Electronics", "Home", "Sports")

SCHEMA = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price_paise INTEGER NOT NULL,
    opening_stock INTEGER NOT NULL,
    stock INTEGER NOT NULL,
    rating REAL NOT NULL
);
CREATE TABLE cart_items (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    UNIQUE (user_id, product_id)
);
CREATE TABLE carts (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    coupon TEXT
);
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    order_no TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    subtotal_paise INTEGER NOT NULL,
    shipping_paise INTEGER NOT NULL,
    discount_paise INTEGER NOT NULL,
    total_paise INTEGER NOT NULL,
    payment_method TEXT NOT NULL,
    status TEXT NOT NULL,
    ship_name TEXT NOT NULL,
    ship_line1 TEXT NOT NULL,
    ship_city TEXT NOT NULL,
    ship_pincode TEXT NOT NULL,
    ship_phone TEXT NOT NULL,
    placed_at TEXT NOT NULL
);
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    product_name TEXT NOT NULL,
    unit_price_paise INTEGER NOT NULL,
    quantity INTEGER NOT NULL
);
"""

# name, category, price in paise, stock, rating
PRODUCTS = [
    ("Cotton Kurta", "Fashion", 79900, 25, 4.2),
    ("Denim Jacket", "Fashion", 189900, 12, 4.0),
    ("Running Shoes", "Sports", 249900, 15, 4.5),
    ("Yoga Mat", "Sports", 59900, 30, 4.3),
    ("Wireless Earbuds", "Electronics", 149900, 20, 4.1),
    ("Bluetooth Speaker", "Electronics", 299900, 8, 4.4),
    ("Smart Watch", "Electronics", 499900, 3, 3.9),
    ("Steel Water Bottle", "Home", 50000, 40, 4.6),
    ("Ceramic Coffee Mug", "Home", 19900, 60, 4.0),
    ("Desk Lamp", "Home", 89900, 0, 3.8),
    ("Laptop Backpack", "Fashion", 129900, 18, 4.2),
    ("Notebook Pack of 5", "Home", 34900, 100, 4.7),
]

SEED_USERS = [
    ("Meera Nair", "meera@example.com", "9876543210", "Meera@123"),
    ("Arjun Das", "arjun@example.com", "9123456780", "Arjun@123"),
]

lock = threading.Lock()
sessions = {}


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 20000).hex()
    return f"{salt}${digest}"


def check_password(password, stored):
    salt = stored.split("$", 1)[0]
    return secrets.compare_digest(hash_password(password, salt), stored)


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def rupees(paise):
    return f"{paise // 100}.{paise % 100:02d}"


def connect():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA case_sensitive_like = ON")
    return conn


db = connect()


def reset_data():
    with lock:
        for table in ("order_items", "orders", "carts", "cart_items", "products", "users"):
            db.execute(f"DROP TABLE IF EXISTS {table}")
        db.executescript(SCHEMA)
        sessions.clear()
        for name, email, phone, password in SEED_USERS:
            db.execute("INSERT INTO users (name, email, phone, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
                       (name, email, phone, hash_password(password), "2026-01-01 09:00:00"))
        for name, category, price, stock, rating in PRODUCTS:
            db.execute("INSERT INTO products (name, category, price_paise, opening_stock, stock, rating)"
                       " VALUES (?, ?, ?, ?, ?, ?)", (name, category, price, stock, stock, rating))


if not db.execute("SELECT name FROM sqlite_master WHERE name = 'users'").fetchone():
    reset_data()


class ApiError(Exception):
    def __init__(self, status, code, message, field=None):
        super().__init__(message)
        self.status, self.code, self.message, self.field = status, code, message, field


def bad(code, message, field=None):
    return ApiError(400, code, message, field)


# ---------- registration and login ----------

def register(body):
    values = {k: body.get(k) for k in ("name", "email", "phone", "password", "confirm_password")}
    for field, value in values.items():
        if not isinstance(value, str) or not value.strip():
            raise bad("REQUIRED_FIELD", f"{field.replace('_', ' ').capitalize()} is required", field)
    name, email, phone = values["name"].strip(), values["email"].strip(), values["phone"].strip()
    password, confirm = values["password"], values["confirm_password"]

    if not re.fullmatch(r"[A-Za-z ]{2,50}", name):
        raise bad("INVALID_NAME", "Name must be 2 to 50 letters", "name")
    if len(email) > 100 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise bad("INVALID_EMAIL", "Enter a valid email address", "email")
    if not re.fullmatch(r"[6-9][0-9]{9}", phone):
        raise bad("INVALID_PHONE", "Phone must be 10 digits starting with 6, 7, 8 or 9", "phone")
    min_len = 8 if FIXED else 9   # build 1.0 wants one character more than the rule says
    if (len(password) < min_len or not re.search(r"[A-Z]", password) or not re.search(r"[a-z]", password)
            or not re.search(r"[0-9]", password) or not re.search(r"[^A-Za-z0-9]", password)):
        raise bad("WEAK_PASSWORD",
                  "Password needs 8 or more characters with upper case, lower case, a digit and a special character",
                  "password")
    if password != confirm:
        raise bad("PASSWORD_MISMATCH", "Passwords do not match", "confirm_password")

    if FIXED:
        email = email.lower()   # 1.0 compares the email exactly as typed
    exists = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if exists:
        raise ApiError(409, "EMAIL_EXISTS", "An account with this email already exists", "email")
    cur = db.execute("INSERT INTO users (name, email, phone, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
                     (name, email, phone, hash_password(password), now()))
    return 201, {"id": cur.lastrowid, "name": name, "email": email}


def login(body):
    email = body.get("email")
    password = body.get("password")
    if not isinstance(email, str) or not email.strip() or not isinstance(password, str) or not password:
        raise bad("REQUIRED_FIELD", "Email and password are required")
    user = db.execute("SELECT * FROM users WHERE lower(email) = ?", (email.strip().lower(),)).fetchone()
    if not user or not check_password(password, user["password_hash"]):
        raise ApiError(401, "INVALID_CREDENTIALS", "Invalid email or password")
    token = secrets.token_hex(16)
    sessions[token] = user["id"]
    return 200, {"token": token, "user": {"name": user["name"], "email": user["email"]}}


# ---------- products ----------

def product_json(p):
    return {"id": p["id"], "name": p["name"], "category": p["category"], "price": rupees(p["price_paise"]),
            "stock": p["stock"], "rating": p["rating"]}


def list_products(query):
    q = query.get("q", [""])[0].strip()
    category = query.get("category", [""])[0]
    sort = query.get("sort", [""])[0]
    if category and category not in CATEGORIES:
        raise bad("INVALID_CATEGORY", "Unknown category", "category")
    if sort and sort not in ("price_asc", "price_desc", "rating"):
        raise bad("INVALID_SORT", "Unknown sort option", "sort")
    if len(q) > 50:
        raise bad("INVALID_QUERY", "Search text can be at most 50 characters", "q")
    sql, args = "SELECT * FROM products WHERE 1 = 1", []
    if q:
        if FIXED:
            escaped = q.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            sql += " AND lower(name) LIKE ? ESCAPE '\\'"
            args.append(f"%{escaped}%")
        else:
            sql += " AND name LIKE ?"
            args.append(f"%{q}%")
    if category:
        sql += " AND category = ?"
        args.append(category)
    sql += {"price_asc": " ORDER BY price_paise ASC", "price_desc": " ORDER BY price_paise DESC",
            "rating": " ORDER BY rating DESC, id"}.get(sort, " ORDER BY id")
    rows = [product_json(p) for p in db.execute(sql, args).fetchall()]
    return 200, {"count": len(rows), "products": rows}


def get_product(product_id):
    p = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone() if product_id.isdigit() else None
    if not p:
        raise ApiError(404, "PRODUCT_NOT_FOUND", "Product not found")
    return 200, product_json(p)


# ---------- cart ----------

def cart_view(user_id):
    rows = db.execute(
        "SELECT p.id, p.name, p.price_paise, c.quantity FROM cart_items c JOIN products p ON p.id = c.product_id"
        " WHERE c.user_id = ? ORDER BY c.id", (user_id,)).fetchall()
    subtotal = sum(r["price_paise"] * r["quantity"] for r in rows)
    coupon = (db.execute("SELECT coupon FROM carts WHERE user_id = ?", (user_id,)).fetchone() or {"coupon": None})["coupon"]
    discount = 0
    if coupon and subtotal >= COUPON_MIN:
        discount = subtotal // 10
        if FIXED:
            discount = min(discount, COUPON_CAP)
    elif coupon:
        db.execute("UPDATE carts SET coupon = NULL WHERE user_id = ?", (user_id,))
        coupon = None
    if not rows:
        shipping = 0
    elif FIXED:
        shipping = 0 if subtotal >= FREE_SHIPPING_FROM else SHIPPING_FEE
    else:
        shipping = 0 if subtotal > FREE_SHIPPING_FROM else SHIPPING_FEE
    total = subtotal - discount + shipping
    return {"items": [{"product_id": r["id"], "name": r["name"], "price": rupees(r["price_paise"]),
                       "quantity": r["quantity"], "line_total": rupees(r["price_paise"] * r["quantity"])}
                      for r in rows],
            "subtotal": rupees(subtotal), "discount": rupees(discount), "shipping": rupees(shipping),
            "total": rupees(total), "coupon": coupon,
            "_paise": {"subtotal": subtotal, "discount": discount, "shipping": shipping, "total": total}}


def public_cart(user_id):
    cart = cart_view(user_id)
    cart.pop("_paise")
    return cart


def parse_qty(raw):
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise bad("INVALID_QUANTITY", "Quantity must be a whole number", "quantity")
    if raw < 1:
        raise bad("INVALID_QUANTITY", "Quantity must be at least 1", "quantity")
    if raw > MAX_QTY:
        raise bad("QUANTITY_LIMIT", f"You can buy at most {MAX_QTY} of one product", "quantity")
    return raw


def find_product(pid):
    p = db.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone() if isinstance(pid, int) else None
    if not p:
        raise ApiError(404, "PRODUCT_NOT_FOUND", "Product not found")
    return p


def add_to_cart(user_id, body):
    product = find_product(body.get("product_id"))
    qty = parse_qty(body.get("quantity", 1))
    if product["stock"] <= 0:
        raise ApiError(409, "OUT_OF_STOCK", "This product is out of stock")
    row = db.execute("SELECT quantity FROM cart_items WHERE user_id = ? AND product_id = ?",
                     (user_id, product["id"])).fetchone()
    new_qty = qty + (row["quantity"] if row else 0)
    if new_qty > MAX_QTY:
        raise bad("QUANTITY_LIMIT", f"You can buy at most {MAX_QTY} of one product", "quantity")
    if new_qty > product["stock"]:
        raise ApiError(409, "INSUFFICIENT_STOCK", f"Only {product['stock']} left in stock")
    if row:
        db.execute("UPDATE cart_items SET quantity = ? WHERE user_id = ? AND product_id = ?",
                   (new_qty, user_id, product["id"]))
    else:
        db.execute("INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)",
                   (user_id, product["id"], qty))
    return 200, public_cart(user_id)


def update_cart(user_id, product_id, body):
    row = db.execute("SELECT * FROM cart_items WHERE user_id = ? AND product_id = ?",
                     (user_id, product_id)).fetchone() if product_id.isdigit() else None
    if not row:
        raise ApiError(404, "ITEM_NOT_IN_CART", "That product is not in your cart")
    qty = parse_qty(body.get("quantity"))
    if FIXED:
        stock = db.execute("SELECT stock FROM products WHERE id = ?", (row["product_id"],)).fetchone()["stock"]
        if qty > stock:
            raise ApiError(409, "INSUFFICIENT_STOCK", f"Only {stock} left in stock")
    db.execute("UPDATE cart_items SET quantity = ? WHERE id = ?", (qty, row["id"]))
    return 200, public_cart(user_id)


def remove_from_cart(user_id, product_id):
    row = db.execute("SELECT id FROM cart_items WHERE user_id = ? AND product_id = ?",
                     (user_id, product_id)).fetchone() if product_id.isdigit() else None
    if not row:
        raise ApiError(404, "ITEM_NOT_IN_CART", "That product is not in your cart")
    db.execute("DELETE FROM cart_items WHERE id = ?", (row["id"],))
    return 200, public_cart(user_id)


def apply_coupon(user_id, body):
    code = body.get("code")
    if not isinstance(code, str) or code.strip().upper() != COUPON_CODE:
        raise bad("INVALID_COUPON", "Coupon code is not valid", "code")
    cart = cart_view(user_id)
    if cart["_paise"]["subtotal"] < COUPON_MIN:
        raise bad("COUPON_MIN_SUBTOTAL", "Coupon needs a cart value of at least 1000.00", "code")
    db.execute("INSERT INTO carts (user_id, coupon) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET coupon = ?",
               (user_id, COUPON_CODE, COUPON_CODE))
    return 200, public_cart(user_id)


def remove_coupon(user_id):
    db.execute("UPDATE carts SET coupon = NULL WHERE user_id = ?", (user_id,))
    return 200, public_cart(user_id)


# ---------- checkout and orders ----------

def checkout(user_id, body):
    cart = cart_view(user_id)
    if not cart["items"]:
        raise bad("EMPTY_CART", "Your cart is empty")
    fields = {}
    for field in ("name", "line1", "city", "pincode", "phone"):
        value = body.get(field)
        if not isinstance(value, str) or not value.strip():
            raise bad("REQUIRED_FIELD", f"{'Address' if field == 'line1' else field.capitalize()} is required", field)
        fields[field] = value.strip()
    pin = fields["pincode"]
    pin_ok = re.fullmatch(r"[1-9][0-9]{5}", pin) if FIXED else re.fullmatch(r"[1-9][0-9]{5,}", pin)
    if not pin_ok:
        raise bad("INVALID_PINCODE", "Pincode must be 6 digits and cannot start with 0", "pincode")
    if not re.fullmatch(r"[6-9][0-9]{9}", fields["phone"]):
        raise bad("INVALID_PHONE", "Phone must be 10 digits starting with 6, 7, 8 or 9", "phone")
    method = body.get("payment_method")
    if method not in ("COD", "UPI"):
        raise bad("INVALID_PAYMENT", "Choose Cash on Delivery or UPI", "payment_method")
    totals = cart["_paise"]
    if method == "COD" and totals["total"] > COD_LIMIT:
        raise bad("COD_NOT_AVAILABLE", "Cash on Delivery is not available above 50000.00", "payment_method")
    if method == "UPI":
        upi = body.get("upi_id")
        if not isinstance(upi, str) or not re.fullmatch(r"[A-Za-z0-9._-]{2,}@[A-Za-z]{2,}", upi.strip()):
            raise bad("INVALID_UPI", "Enter a valid UPI id like name@bank", "upi_id")

    lines = db.execute(
        "SELECT p.id, p.name, p.price_paise, p.stock, c.quantity FROM cart_items c"
        " JOIN products p ON p.id = c.product_id WHERE c.user_id = ? ORDER BY c.id", (user_id,)).fetchall()
    if FIXED:
        for line in lines:
            if line["quantity"] > line["stock"]:
                raise ApiError(409, "INSUFFICIENT_STOCK", f"Only {line['stock']} of {line['name']} left in stock")

    stamp = now()
    db.execute("BEGIN")
    try:
        last = db.execute("SELECT COUNT(*) AS n FROM orders").fetchone()["n"]
        order_no = f"ORD{100001 + last}"
        cur = db.execute(
            "INSERT INTO orders (order_no, user_id, subtotal_paise, shipping_paise, discount_paise, total_paise,"
            " payment_method, status, ship_name, ship_line1, ship_city, ship_pincode, ship_phone, placed_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, 'PLACED', ?, ?, ?, ?, ?, ?)",
            (order_no, user_id, totals["subtotal"], totals["shipping"], totals["discount"], totals["total"], method,
             fields["name"], fields["line1"], fields["city"], pin, fields["phone"], stamp))
        for line in lines:
            db.execute("INSERT INTO order_items (order_id, product_id, product_name, unit_price_paise, quantity)"
                       " VALUES (?, ?, ?, ?, ?)", (cur.lastrowid, line["id"], line["name"], line["price_paise"],
                                                   line["quantity"]))
            db.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (line["quantity"], line["id"]))
        db.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
        db.execute("UPDATE carts SET coupon = NULL WHERE user_id = ?", (user_id,))
        db.execute("COMMIT")
    except Exception:
        db.execute("ROLLBACK")
        raise
    return 201, order_detail_json(db.execute("SELECT * FROM orders WHERE id = ?", (cur.lastrowid,)).fetchone())


def order_detail_json(o):
    items = db.execute("SELECT * FROM order_items WHERE order_id = ? ORDER BY id", (o["id"],)).fetchall()
    return {"order_no": o["order_no"], "status": o["status"], "placed_at": o["placed_at"],
            "payment_method": o["payment_method"],
            "subtotal": rupees(o["subtotal_paise"]), "discount": rupees(o["discount_paise"]),
            "shipping": rupees(o["shipping_paise"]), "total": rupees(o["total_paise"]),
            "address": {"name": o["ship_name"], "line1": o["ship_line1"], "city": o["ship_city"],
                        "pincode": o["ship_pincode"], "phone": o["ship_phone"]},
            "items": [{"product": i["product_name"], "price": rupees(i["unit_price_paise"]),
                       "quantity": i["quantity"]} for i in items]}


def list_orders(user_id):
    rows = db.execute("SELECT o.*, (SELECT COALESCE(SUM(quantity), 0) FROM order_items WHERE order_id = o.id) AS n"
                      " FROM orders o WHERE user_id = ? ORDER BY id DESC", (user_id,)).fetchall()
    out = []
    for o in rows:
        shown = o["total_paise"] if FIXED else o["subtotal_paise"] - o["discount_paise"]
        out.append({"order_no": o["order_no"], "placed_at": o["placed_at"], "status": o["status"],
                    "item_count": o["n"], "total": rupees(shown)})
    return 200, {"orders": out}


def get_order(user_id, order_no):
    o = db.execute("SELECT * FROM orders WHERE order_no = ?", (order_no,)).fetchone()
    if not o or (FIXED and o["user_id"] != user_id):
        raise ApiError(404, "ORDER_NOT_FOUND", "Order not found")
    return 200, order_detail_json(o)


# ---------- http ----------

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def send(self, status, payload):
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def user_id(self):
        header = self.headers.get("Authorization", "")
        token = header[7:] if header.startswith("Bearer ") else ""
        uid = sessions.get(token)
        if not uid:
            raise ApiError(401, "UNAUTHORIZED", "Please log in")
        return uid

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            raise bad("BAD_JSON", "Request body is not valid JSON")
        if not isinstance(body, dict):
            raise bad("BAD_JSON", "Request body must be a JSON object")
        return body

    def serve_file(self, name):
        types = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
                 ".css": "text/css; charset=utf-8"}
        path = HERE / "static" / name
        if not path.is_file():
            raise ApiError(404, "NOT_FOUND", "No such page")
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", types[path.suffix])
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def route(self, method):
        url = urlparse(self.path)
        parts = [unquote(p) for p in url.path.split("/") if p]
        query = parse_qs(url.query)
        if method == "GET" and not parts:
            return self.serve_file("index.html")
        if method == "GET" and len(parts) == 1 and parts[0] in ("app.js", "style.css"):
            return self.serve_file(parts[0])
        if parts[:1] != ["api"]:
            raise ApiError(404, "NOT_FOUND", "No such endpoint")
        rest = parts[1:]
        if method == "GET" and rest == ["health"]:
            return self.send(200, {"status": "ok", "build": BUILD})
        if method == "POST" and rest == ["register"]:
            return self.send(*register(self.read_json()))
        if method == "POST" and rest == ["login"]:
            return self.send(*login(self.read_json()))
        if method == "GET" and rest == ["products"]:
            return self.send(*list_products(query))
        if method == "GET" and len(rest) == 2 and rest[0] == "products":
            return self.send(*get_product(rest[1]))
        if rest[:1] == ["cart"]:
            uid = self.user_id()
            if method == "GET" and rest == ["cart"]:
                return self.send(200, public_cart(uid))
            if method == "POST" and rest == ["cart", "items"]:
                return self.send(*add_to_cart(uid, self.read_json()))
            if method == "PUT" and len(rest) == 3 and rest[1] == "items":
                return self.send(*update_cart(uid, rest[2], self.read_json()))
            if method == "DELETE" and len(rest) == 3 and rest[1] == "items":
                return self.send(*remove_from_cart(uid, rest[2]))
            if method == "POST" and rest == ["cart", "coupon"]:
                return self.send(*apply_coupon(uid, self.read_json()))
            if method == "DELETE" and rest == ["cart", "coupon"]:
                return self.send(*remove_coupon(uid))
        if method == "POST" and rest == ["checkout"]:
            uid = self.user_id()
            return self.send(*checkout(uid, self.read_json()))
        if method == "GET" and rest == ["orders"]:
            return self.send(*list_orders(self.user_id()))
        if method == "GET" and len(rest) == 2 and rest[0] == "orders":
            return self.send(*get_order(self.user_id(), rest[1]))
        raise ApiError(404, "NOT_FOUND", "No such endpoint")

    def handle_request(self, method):
        try:
            if method == "POST" and urlparse(self.path).path == "/api/dev/reset":
                reset_data()
                return self.send(200, {"status": "reset", "build": BUILD})
            with lock:
                return self.route(method)
        except ApiError as err:
            body = {"error": err.message, "code": err.code}
            if err.field:
                body["field"] = err.field
            self.send(err.status, body)
        except Exception:
            self.send(500, {"error": "Internal server error"})

    def do_GET(self):
        self.handle_request("GET")

    def do_POST(self):
        self.handle_request("POST")

    def do_PUT(self):
        self.handle_request("PUT")

    def do_DELETE(self):
        self.handle_request("DELETE")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"shop build {BUILD} on http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
