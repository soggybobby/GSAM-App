import mysql.connector

# --- Database Connection ---
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="inventory_db"
    )

# --- User Login ---
def login_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "SELECT id, role FROM users WHERE username=%s AND password=%s"
    cursor.execute(sql, (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        user_id, role = user
        print(f"Logged in as {role}")
        return {"user_id": user_id, "role": role}
    else:
        print("Invalid credentials.")
        return None

# --- Add New Product ---
def add_product(name, quantity, price, expiration_date):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO products (name, quantity, price, expiration_date) VALUES (%s, %s, %s, %s)"
    cursor.execute(sql, (name, quantity, price, expiration_date))
    conn.commit()
    conn.close()

# --- View All Products ---
def view_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    results = cursor.fetchall()
    conn.close()
    return results

# --- Update Product ---
def update_product(product_id, name, quantity, price, expiration_date):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "UPDATE products SET name=%s, quantity=%s, price=%s, expiration_date=%s WHERE id=%s"
    cursor.execute(sql, (name, quantity, price, expiration_date, product_id))
    conn.commit()
    conn.close()

# --- Delete Product ---
def delete_product(product_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=%s", (product_id,))
    conn.commit()
    conn.close()

# --- Log Stock In/Out ---
def log_stock(product_id, qty, log_type, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO stock_logs (product_id, type, quantity, user_id) VALUES (%s, %s, %s, %s)"
    cursor.execute(sql, (product_id, log_type, qty, user_id))

    if log_type == "in":
        cursor.execute("UPDATE products SET quantity = quantity + %s WHERE id = %s", (qty, product_id))
    elif log_type == "out":
        cursor.execute("UPDATE products SET quantity = quantity - %s WHERE id = %s", (qty, product_id))

    conn.commit()
    conn.close()
