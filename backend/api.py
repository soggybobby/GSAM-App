from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="inventory_db"
    )

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data["username"]
    password = data["password"]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, role FROM users WHERE username=%s AND password=%s", (username, password))
    user = cursor.fetchone()
    conn.close()
    if user:
        return jsonify({"user_id": user[0], "role": user[1]})
    return "Invalid credentials", 401

@app.route("/products", methods=["GET"])
def products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    result = cursor.fetchall()
    conn.close()
    return jsonify(result)

@app.route("/stocklog", methods=["POST"])
def stocklog():
    data = request.get_json()
    product_id = data["product_id"]
    qty = data["quantity"]
    log_type = data["type"]
    user_id = data["user_id"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO stock_logs (product_id, type, quantity, user_id) VALUES (%s, %s, %s, %s)",
                   (product_id, log_type, qty, user_id))

    if log_type == "in":
        cursor.execute("UPDATE products SET quantity = quantity + %s WHERE id = %s", (qty, product_id))
    elif log_type == "out":
        cursor.execute("UPDATE products SET quantity = quantity - %s WHERE id = %s", (qty, product_id))

    conn.commit()
    conn.close()
    return "Stock logged", 200

if __name__ == "__main__":
    app.run(debug=True)
