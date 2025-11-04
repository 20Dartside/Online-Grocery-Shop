import os
import json
from datetime import datetime
import MySQLdb   # <— note: using MySQLdb (not mysql.connector)
from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify
from werkzeug.security import generate_password_hash , check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

USER_FILE = "users.json"

# ============================================================
# ✅ MYSQL CONFIG (edit these only once)
# ============================================================
app.config['MYSQL_HOST'] = 'localhost'        #  your AWS RDS endpoint /ipaddress
app.config['MYSQL_USER'] = 'root'             # MySQL username
app.config['MYSQL_PASSWORD'] = 'root'  # MySQL password
app.config['MYSQL_DB'] = 'mydatabase'


# ============================================================
# ✅ COMMON DB CONNECTION FUNCTION (used everywhere)
# ============================================================
def get_db_connection(with_db=True):
    """
    Returns a MySQLdb connection.
    If with_db=False → connects without database (for creating DB).
    """
    if with_db:
        return MySQLdb.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            passwd=app.config['MYSQL_PASSWORD'],
            db=app.config['MYSQL_DB']
        )
    else:
        return MySQLdb.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            passwd=app.config['MYSQL_PASSWORD']
        )


# ============================================================
# ✅ INIT DB (AUTO CREATE DATABASE + TABLES)
# ============================================================
def init_db():
    try:
        # Step 1: Connect without DB and create the database
        db = get_db_connection(with_db=False)
        cursor = db.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS mydatabase;")
        cursor.execute("USE mydatabase;")  # ✅ Select the DB before doing anything
        print("✅ Database created or verified.")
        
        # Step 2: Create the users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                username VARCHAR(100) UNIQUE,
                email VARCHAR(255) UNIQUE,
                password VARCHAR(255),
                role VARCHAR(50) DEFAULT 'user',
                last_login DATETIME
            )
        """)

        # Step 3: Create the checkout table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkout (
                id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(255),
                phone VARCHAR(20) UNIQUE,
                email VARCHAR(255) UNIQUE,
                address TEXT,
                city VARCHAR(100),
                pin VARCHAR(10),
                payment VARCHAR(50),
                username VARCHAR(100),
                cart JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        db.commit()

        # Step 4: Check and hash old plaintext passwords (if any)
        cursor.execute("SELECT id, password FROM users")
        users = cursor.fetchall()
        for user_id, password in users:
            if not password.startswith("pbkdf2:sha256:"):
                hashed = generate_password_hash(password)
                cursor.execute("UPDATE users SET password=%s WHERE id=%s", (hashed, user_id))
                print(f"🔒 Password hashed for user id={user_id}")
            else:
                print(f"ℹ Already hashed: user id={user_id}")

        # Step 5: Ensure admin user exists in DB
        cursor.execute("SELECT * FROM users WHERE username=%s", ("admin",))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO users (name, username, email, password, role, last_login)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, ("Administrator", "admin", "admin@example.com", generate_password_hash("admin123"), "admin", None))
            print("✅ Admin user created: username='admin', password='admin123'")

        db.commit()

        # Step 6: Ensure admin exists in users.json
        try:
            users_data = {}
            if os.path.exists(USER_FILE):
                with open(USER_FILE, "r") as f:
                    txt = f.read().strip()
                    if txt:
                        users_data = json.loads(txt)

            # ⚠️ Warning: password in users.json must also be hashed, or ignored during login
            users_data["admin"] = {
                "name": "Administrator",
                "email": "admin@example.com",
                "username": "admin",
                "password": generate_password_hash("admin123"),
                "role": "admin"
            }

            with open(USER_FILE, "w") as f:
                json.dump(users_data, f, indent=2)
            print("✅ Admin entry ensured in users.json")
        except Exception as je:
            print("⚠ Could not update users.json:", je)

        # Clean up
        cursor.close()
        db.close()
        print("✅ Tables created and users verified.")

    except Exception as e:
        print("❌ Database init error:", e)


# 🔁 Call the function at startup
init_db()


# ============================================================
# ✅ HELPER FUNCTIONS
# ============================================================
def load_users():
    """Load users.json safely (auto-create if missing)."""
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w") as f:
            json.dump({}, f, indent=2)
        print("📄 users.json created (empty).")
        return {}

    try:
        with open(USER_FILE, "r") as f:
            data = f.read().strip()
            if not data:
                return {}
            return json.loads(data)
    except json.JSONDecodeError:
        print("⚠ users.json was corrupted; recreated.")
        with open(USER_FILE, "w") as f:
            json.dump({}, f, indent=2)
        return {}

def save_users(users):
    """Save users dictionary safely to users.json"""
    import json
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)



def ensure_user_in_json(username, name, email, password, role="user"):
    """Ensure that each user who logs in or signs up exists in users.json."""
    users = load_users()
    users[username] = {
        "name": name,
        "email": email,
        "username": username,
        "password": password,
        "role": role
    }
    save_users(users)


# ============================================================
# ✅ ROUTES START
# ============================================================

@app.route('/shopall')
def shopall():
    return render_template('shopall.html')

@app.route('/snacks')
def snacks():
    return render_template('snacks.html')

@app.route('/chuda')
def chuda():
    return render_template('chuda.html')

@app.route('/poha')
def poha():
    return render_template('poha.html')

@app.route('/namkeen')
def namkeen():
    return render_template('namkeen.html')

@app.route('/products')
def products():
    return render_template('products.html')

@app.route('/order')
def order():
    return render_template('order.html')

'''@app.route('/cart')
def cart():
    return render_template('cart.html')'''

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/wishlist')
def wishlist():
    return render_template('wishlist.html')

@app.route('/about')
def about():
    return render_template('about.html')


# ============================================================
# ✅ LOGIN / SIGNUP
# ============================================================

@app.route("/", methods=["GET", "POST"])
def login():
    db = get_db_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    if request.method == "POST":
        action = request.form.get("action")

        if action == "signup":
            # === SIGNUP HANDLER ===
            name = request.form["name"].strip()
            username = request.form["username"].strip()
            email = request.form["email"].strip()
            password = request.form["password"].strip()

            # Check if username exists
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash("⚠️ Username already exists! Please login.", "error")
            else:
                hashed_password = generate_password_hash(password)
                cursor.execute("""
                    INSERT INTO users (name, username, email, password, role, last_login)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (name, username, email, hashed_password, "user", None))
                db.commit()

                ensure_user_in_json(username, name, email, hashed_password, "user")
                flash("✅ Signup successful! Please login now.", "success")

        elif action == "login":
            # === LOGIN HANDLER (PASSWORD CHECK BYPASSED FOR DEBUGGING) ===
            username = request.form["username"].strip()
            password = request.form["password"].strip()

            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

            if not user:
                flash("⚠️ User not found! Please sign up first.", "error")
            else:
                # ---- BYPASS PASSWORD CHECK (FOR DEBUGGING) ----
                # This will log in any existing username regardless of password.
                session["username"] = username
                session["role"] = user.get("role", "user")

                # Update last login timestamp
                cursor.execute("UPDATE users SET last_login = %s WHERE username = %s",
                               (datetime.now(), username))
                db.commit()

                ensure_user_in_json(user["username"], user["name"], user["email"],
                                    user["password"], user["role"])

                flash("✅ Login successful! (Password check bypassed)", "success")

                cursor.close()
                db.close()

                if user["role"] == "admin":
                    return redirect(url_for("admin_dashboard"))
                else:
                    return redirect(url_for("index"))

    # GET request or failed POST
    cursor.close()
    db.close()
    return render_template("login.html")

# ============================================================
# ✅ INDEX PAGE
# ============================================================
@app.route("/index")
def index():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", username=session["username"])


# ============================================================
# ✅ PROFILE PAGE
# ============================================================
@app.route("/profile")
def profile():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT name, username, role, last_login FROM users WHERE username=%s", (username,))
    user = cursor.fetchone()
    cursor.close()
    db.close()

    user_data = {
        "name": user[0],
        "username": user[1],
        "role": user[2],
        "last_login": user[3]
    }

    return render_template("profile.html", user=user_data, username=username)


# ============================================================
# ✅ LOGOUT
# ============================================================
@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ============================================================
# ✅ ADMIN DASHBOARD
# ============================================================
@app.route("/admin")
def admin_dashboard():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]

    # Check role from session directly (faster)
    if session.get("role") != "admin":
        flash("❌ Access denied! Only admins allowed.", "error")
        return redirect(url_for("index"))

    db = get_db_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    # ✅ Fetch all non-admin users
    cursor.execute("SELECT id, name, username, email, password, role, last_login FROM users WHERE role != 'admin'")
    users = cursor.fetchall()

    # ✅ Fetch all checkout orders
    cursor.execute("SELECT id, full_name, phone, email, address, city, pin, payment, username, created_at FROM checkout")
    orders = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "admin_dashboard.html",
        username=username,
        users=users,
        orders=orders
    )


@app.route("/add_user", methods=["POST"])
def add_user():
    if session.get("role") != "admin":
        return jsonify(success=False, message="Access denied!")

    # ✅ Support both form submission and JSON
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    name = data.get("name")
    email = data.get("email")
    username = data.get("username")
    password = data.get("password")
    role = data.get("role")

    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (name, email, username, password, role)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, email, username, generate_password_hash(password), role))
        db.commit()
        return jsonify(success=True, message="✅ User added successfully!")
    except MySQLdb.IntegrityError:
        return jsonify(success=False, message="⚠️ Username or email already exists!")
    finally:
        cursor.close()
        db.close()

@app.route("/delete_user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    if session.get("role") != "admin":
        return jsonify(success=False, message="Access denied!")

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    db.commit()
    cursor.close()
    db.close()
    return jsonify(success=True, message="🗑️ User deleted successfully!")

@app.route("/reset_password/<int:user_id>", methods=["POST"])
def reset_password(user_id):
    if session.get("role") != "admin":
        return jsonify(success=False, message="Access denied!")

    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    new_password = data.get("new_password")

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("UPDATE users SET password = %s WHERE id = %s",
                   (generate_password_hash(new_password), user_id))
    db.commit()
    cursor.close()
    db.close()
    return jsonify(success=True, message="🔑 Password reset successfully!")

# ============================================================
# ✅ SAVE CHECKOUT
# ============================================================
@app.route("/save_checkout", methods=["POST"])
def save_checkout():
    try:
        data = request.json
        username = session.get("username")
        if not username:
            return jsonify({"status":"error","msg":"User not logged in"}), 401

        cart_json = json.dumps(data.get("cart", []))  # Convert cart array to JSON string

        db = get_db_connection()
        cursor = db.cursor()

        # Check if 'cart' column exists
        cursor.execute("SHOW COLUMNS FROM checkout LIKE 'cart'")
        result = cursor.fetchone()
        if not result:
            cursor.execute("ALTER TABLE checkout ADD COLUMN cart JSON")
            db.commit()
            print("✅ 'cart' column added to checkout table")

        # Insert checkout data
        sql = """
            INSERT INTO checkout
            (full_name, phone, email, address, city, pin, payment, username, cart)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            data.get("full_name"),
            data.get("phone"),
            data.get("email"),
            data.get("address"),
            data.get("city"),
            data.get("pin"),
            data.get("payment"),
            username,
            cart_json
        ))

        db.commit()
        cursor.close()
        db.close()

        return jsonify({"status":"success","msg":"Checkout saved successfully!"})

    except Exception as e:
        print("❌ Error saving checkout:", e)
        return jsonify({"status":"error","msg":str(e)}), 500



@app.route('/cart')
def cart():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    db = get_db_connection()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("SELECT cart FROM checkout WHERE username=%s ORDER BY id DESC LIMIT 1", (username,))
    row = cursor.fetchone()
    cursor.close()
    db.close()

    cart_items = []
    if row and row['cart']:
        cart_items = json.loads(row['cart'])  # parse JSON to Python list/dict

    return render_template('cart.html', cart_items=cart_items)



# ============================================================
# ✅ RUN APP
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
