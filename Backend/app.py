from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import bcrypt
import os

app = Flask(__name__)

# Allow frontend requests
CORS(app, resources={r"/api/*": {"origins": os.environ.get("FRONTEND_ORIGIN", "*")}})


# MySQL CONFIGURATION

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 3306)),
    "user": os.environ.get("DB_USER", "auth_user"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "authentication_db")
}


# DATABASE CONNECTION

def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)

        if connection.is_connected():
            return connection

    except Error as e:
        print("Database connection error:", e)

    return None


# HOME PAGE

@app.route("/")
def home():
    return render_template("index.html")


# TEST DATABASE CONNECTION

@app.route("/api/test-db", methods=["GET"])
def test_database():
    connection = get_db_connection()

    if connection is None:
        return jsonify({
            "success": False,
            "message": "Could not connect to MySQL"
        }), 500

    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE()")
        database = cursor.fetchone()[0]

        return jsonify({
            "success": True,
            "message": "MySQL connection successful",
            "database": database
        })

    except Error as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if connection:
            try:
                connection.close()
            except Exception:
                pass


# REGISTER

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received"
        }), 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # Validate name
    if not name:
        return jsonify({
            "success": False,
            "message": "Name is required"
        }), 400

    # Validate email
    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required"
        }), 400

    # Validate password
    if not password:
        return jsonify({
            "success": False,
            "message": "Password is required"
        }), 400

    if len(password) < 6:
        return jsonify({
            "success": False,
            "message": "Password must be at least 6 characters"
        }), 400

    connection = get_db_connection()

    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed"
        }), 500

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)

        # Check whether email already exists
        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            return jsonify({
                "success": False,
                "message": "Email is already registered"
            }), 409

        # Hash password
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        # Insert user
        cursor.execute(
            """
            INSERT INTO users (name, email, password)
            VALUES (%s, %s, %s)
            """,
            (name, email, password_hash)
        )

        connection.commit()

        user_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": "Registration successful",
            "user": {
                "id": user_id,
                "name": name,
                "email": email
            }
        }), 201

    except Error as e:
        if connection:
            connection.rollback()

        print("Registration error:", e)

        return jsonify({
            "success": False,
            "message": "Registration failed"
        }), 500

    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if connection:
            try:
                connection.close()
            except Exception:
                pass


# LOGIN


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received"
        }), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required"
        }), 400

    if not password:
        return jsonify({
            "success": False,
            "message": "Password is required"
        }), 400

    connection = get_db_connection()

    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed"
        }), 500

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, name, email, password
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        user = cursor.fetchone()

        # User doesn't exist
        if not user:
            return jsonify({
                "success": False,
                "message": "Invalid email or password"
            }), 401

        # Check password
        password_valid = bcrypt.checkpw(
            password.encode("utf-8"),
            user["password"].encode("utf-8")
        )

        if not password_valid:
            return jsonify({
                "success": False,
                "message": "Invalid email or password"
            }), 401

        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"]
            }
        }), 200

    except Error as e:
        print("Login error:", e)

        return jsonify({
            "success": False,
            "message": "Login failed"
        }), 500

    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if connection:
            try:
                connection.close()
            except Exception:
                pass


# GET ALL USERS

@app.route("/api/users", methods=["GET"])
def get_users():
    connection = get_db_connection()

    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed"
        }), 500

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, name, email, created_at
            FROM users
            ORDER BY id DESC
            """
        )

        users = cursor.fetchall()

        return jsonify({
            "success": True,
            "users": users
        })

    except Error as e:
        print("Get users error:", e)

        return jsonify({
            "success": False,
            "message": "Could not fetch users"
        }), 500

    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if connection:
            try:
                connection.close()
            except Exception:
                pass


# PROFILE PAGE

@app.route("/profile")
def profile():
    return render_template("profile.html")


# RUN FLASK

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        debug=False
    )