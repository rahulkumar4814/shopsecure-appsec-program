import hashlib
import os
import time

import httpx
import jwt
import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="orders-api (v1, deliberately weak)")

JWT_SECRET = "secret123"
PAYMENTS_URL = os.getenv("PAYMENTS_URL", "http://payments-svc:8002")


def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        dbname=os.getenv("DB_NAME", "shop"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )


class Creds(BaseModel):
    username: str
    password: str


class OrderIn(BaseModel):
    user_id: int
    product_id: int
    quantity: int
    card_number: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/register")
def register(c: Creds):
    pw = hashlib.md5(c.password.encode()).hexdigest()
    conn = get_conn()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id",
                (c.username, pw),
            )
            return {"id": cur.fetchone()[0], "username": c.username}
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(409, "username already exists")
    finally:
        conn.close()


@app.post("/login")
def login(c: Creds):
    pw = hashlib.md5(c.password.encode()).hexdigest()
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, role FROM users WHERE username=%s AND password_hash=%s",
                (c.username, pw),
            )
            row = cur.fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(401, "bad credentials")
    token = jwt.encode(
        {"sub": str(row[0]), "role": row[1], "iat": int(time.time())},
        JWT_SECRET,
        algorithm="HS256",
    )
    return {"access_token": token}


@app.get("/products")
def products(search: str = ""):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT id, name, price FROM products WHERE name ILIKE '%" + search + "%'")
            return cur.fetchall()
    except Exception as e:
        raise HTTPException(500, f"query failed: {e}")
    finally:
        conn.close()


@app.post("/orders")
def create_order(o: OrderIn):
    conn = get_conn()
    try:
        with conn, conn.cursor() as cur:
            cur.execute("SELECT price FROM products WHERE id=%s", (o.product_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "product not found")
            total = float(row[0]) * o.quantity
            cur.execute(
                "INSERT INTO orders (user_id, product_id, quantity, total) VALUES (%s,%s,%s,%s) RETURNING id",
                (o.user_id, o.product_id, o.quantity, total),
            )
            order_id = cur.fetchone()[0]
            r = httpx.post(
                f"{PAYMENTS_URL}/charge",
                json={"order_id": order_id, "amount": total, "card_number": o.card_number},
                timeout=5,
            )
            status = r.json()["status"]
            cur.execute("UPDATE orders SET status=%s WHERE id=%s", (status, order_id))
            return {"order_id": order_id, "total": total, "status": status}
    finally:
        conn.close()


@app.get("/orders/{order_id}")
def get_order(order_id: int):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM orders WHERE id=%s", (order_id,))
            row = cur.fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(404, "order not found")
    return row
