from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)

# --- DB Connection ---
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Default for XAMPP
        database="inventory_db"
    )

# --- User Login ---
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data["username"]
    password = data["password"]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, role FROM users WHERE username=%s AND password=%s", (username, password))
    result = cursor.fetchone()
    conn.close()

    if result:
        return jsonify({"user_id": result[0], "role": result[1]})
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# --- Get All Products ---
@app.route("/products", methods=["GET"])
def get_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return jsonify(products)

# --- Add Product ---
@app.route("/add_product", methods=["POST"])
def add_product():
    data = request.get_json()
    name = data["name"]
    quantity = data["quantity"]
    price = data["price"]
    expiration = data["expiration_date"]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO products (name, quantity, price, expiration_date) VALUES (%s, %s, %s, %s)",
        (name, quantity, price, expiration)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Product added successfully."}), 200

# --- Delete Product by ID ---
@app.route("/delete_product", methods=["POST"])
def delete_product():
    data = request.get_json()
    product_id = data["product_id"]

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Product deleted successfully."})

# --- Get Product by Name (Case-insensitive) ---
@app.route("/get_product_by_name", methods=["POST"])
def get_product_by_name():
    data = request.get_json()
    name = data["name"]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products WHERE LOWER(name) = LOWER(%s) LIMIT 1", (name,))
    product = cursor.fetchone()
    conn.close()

    if product:
        return jsonify(product)
    else:
        return jsonify({"error": "Product not found"}), 404

# --- Record Stock In/Out ---
@app.route("/stocklog", methods=["POST"])
def stock_log():
    data = request.get_json()
    product_id = data["product_id"]
    quantity = data["quantity"]
    log_type = data["type"]
    user_id = data["user_id"]

    conn = get_connection()
    cursor = conn.cursor()

    # Insert log
    cursor.execute(
        "INSERT INTO stock_logs (product_id, type, quantity, user_id) VALUES (%s, %s, %s, %s)",
        (product_id, log_type, quantity, user_id)
    )

    # Update quantity
    if log_type == "in":
        cursor.execute("UPDATE products SET quantity = quantity + %s WHERE id = %s", (quantity, product_id))
    elif log_type == "out":
        cursor.execute("UPDATE products SET quantity = quantity - %s WHERE id = %s", (quantity, product_id))

    conn.commit()
    conn.close()
    return jsonify({"message": "Stock updated."}), 200

# --- View Transaction Logs ---
@app.route("/transaction_logs", methods=["GET"])
def transaction_logs():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.timestamp, s.type, s.quantity, p.name AS product_name
        FROM stock_logs s
        JOIN products p ON s.product_id = p.id
        ORDER BY s.timestamp DESC
        LIMIT 20
    """)
    logs = cursor.fetchall()
    conn.close()
    return jsonify(logs)

@app.route('/search_products', methods=['POST'])
def search_products():
    data = request.get_json()
    query = data.get("query", "")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM products WHERE name LIKE %s LIMIT 10", (f"%{query}%",))
    results = cursor.fetchall()
    conn.close()

    # Flatten list of tuples to list of names
    return jsonify([row[0] for row in results])


# --- Run the Server ---
if __name__ == "__main__":
    app.run(debug=True)
