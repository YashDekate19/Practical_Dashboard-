from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import mysql.connector
from mysql.connector import Error
import bcrypt
import os

app = Flask(__name__)

# Secret key for sessions and token signing
SECRET_KEY = os.environ.get("SECRET_KEY", "prod-secret-key-change-me")
app.secret_key = SECRET_KEY

# Token serializer for stateless authentication
serializer = URLSafeTimedSerializer(SECRET_KEY)

def generate_token(user_id, email):
    """Generate a signed authentication token."""
    return serializer.dumps({"user_id": user_id, "email": email}, salt="auth-salt")

def verify_token(token, max_age=604800):  # Valid for 7 days
    """Verify the signed authentication token."""
    try:
        return serializer.loads(token, salt="auth-salt", max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None

def get_authenticated_user():
    """Extract and verify token from Authorization header (Bearer <token>)."""
    auth_header = request.headers.get("Authorization", "").strip()
    if not auth_header:
        return None

    parts = auth_header.split(" ")
    if len(parts) == 2 and parts[0].lower() == "bearer":
        token = parts[1]
    else:
        token = auth_header

    return verify_token(token)


# -------------------------------------------------------------
# CORS CONFIGURATION
# Configured with user's specific Netlify frontend URL.
# Wildcard is disallowed when origin is specified.
# Credentials are set to False (cookie authentication is not used).
# -------------------------------------------------------------
frontend_origin_env = os.environ.get("FRONTEND_ORIGIN", "").strip()

if frontend_origin_env and frontend_origin_env != "*":
    allowed_origins = [orig.strip() for orig in frontend_origin_env.split(",") if orig.strip()]
else:
    # If FRONTEND_ORIGIN is not provided, allow localhost development ports
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8899",
        "http://127.0.0.1:8899",
        "http://localhost:5500",
        "http://127.0.0.1:5500"
    ]

CORS(
    app,
    resources={r"/api/*": {"origins": allowed_origins}},
    supports_credentials=False,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-Admin-Key"]
)


# -------------------------------------------------------------
# DATABASE CONNECTION
# -------------------------------------------------------------
def get_db_config():
    """Retrieve database configuration from environment variables."""
    raw_port = os.environ.get("DB_PORT", "3306")
    try:
        port = int(raw_port)
    except (ValueError, TypeError):
        port = 3306

    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": port,
        "user": os.environ.get("DB_USER", "auth_user"),
        "password": os.environ.get("DB_PASSWORD", ""),
        "database": os.environ.get("DB_NAME", "authentication_db"),
        "connection_timeout": 10
    }


def get_db_connection():
    """Establish and return a MySQL database connection, or None on failure."""
    try:
        config = get_db_config()
        connection = mysql.connector.connect(**config)
        if connection.is_connected():
            return connection
    except Error as e:
        print("Database connection error:", e)
    except Exception as e:
        print("Unexpected database error:", e)

    return None


# -------------------------------------------------------------
# ROUTES
# -------------------------------------------------------------

@app.route("/")
def home():
    """Render home template."""
    return render_template("index.html")


@app.route("/profile")
def profile():
    """Render profile template."""
    return render_template("profile.html")


@app.route("/api/health", methods=["GET"])
def health():
    """Service liveness probe."""
    return jsonify({
        "success": True,
        "status": "healthy",
        "service": "auth-flask-api"
    }), 200


@app.route("/api/test-db", methods=["GET"])
def test_database():
    """Verify MySQL connectivity and return active database name."""
    connection = get_db_connection()

    if connection is None:
        return jsonify({
            "success": False,
            "message": "Could not connect to MySQL. Check database service status and credentials."
        }), 500

    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE()")
        row = cursor.fetchone()
        database = row[0] if row else None

        return jsonify({
            "success": True,
            "message": "MySQL connection successful",
            "database": database
        }), 200

    except Exception as e:
        print("Test database query error:", e)
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


@app.route("/api/register", methods=["POST"])
def register():
    """Register a new user account with hashed password."""
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received"
        }), 400

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not name:
        return jsonify({
            "success": False,
            "message": "Name is required"
        }), 400

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

        # Hash password using bcrypt
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        # Insert user into MySQL
        cursor.execute(
            """
            INSERT INTO users (name, email, password)
            VALUES (%s, %s, %s)
            """,
            (name, email, password_hash)
        )
        connection.commit()

        user_id = cursor.lastrowid
        token = generate_token(user_id, email)

        return jsonify({
            "success": True,
            "message": "Registration successful",
            "token": token,
            "user": {
                "id": user_id,
                "name": name,
                "email": email
            }
        }), 201

    except Exception as e:
        if connection:
            try:
                connection.rollback()
            except Exception:
                pass
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


@app.route("/api/login", methods=["POST"])
def login():
    """Authenticate user credentials and issue signed token."""
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received"
        }), 400

    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

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

        if not user:
            return jsonify({
                "success": False,
                "message": "Invalid email or password"
            }), 401

        # Check bcrypt password hash
        try:
            password_valid = bcrypt.checkpw(
                password.encode("utf-8"),
                user["password"].encode("utf-8")
            )
        except Exception:
            password_valid = False

        if not password_valid:
            return jsonify({
                "success": False,
                "message": "Invalid email or password"
            }), 401

        token = generate_token(user["id"], user["email"])

        return jsonify({
            "success": True,
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"]
            }
        }), 200

    except Exception as e:
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


@app.route("/api/profile", methods=["GET"])
def get_profile():
    """Retrieve profile data ONLY for the authenticated user.
    Prevents unauthorized access to other users' details."""
    auth_data = get_authenticated_user()

    if not auth_data:
        return jsonify({
            "success": False,
            "message": "Authentication required. Please provide a valid Bearer token."
        }), 401

    auth_user_id = auth_data.get("user_id")
    auth_email = auth_data.get("email")

    # If parameters are supplied, strictly enforce ownership matching
    req_id = request.args.get("id")
    req_email = request.args.get("email", "").strip().lower()

    if req_id and str(req_id) != str(auth_user_id):
        return jsonify({
            "success": False,
            "message": "Forbidden: You are not authorized to view another user's profile."
        }), 403

    if req_email and req_email != auth_email.lower():
        return jsonify({
            "success": False,
            "message": "Forbidden: You are not authorized to view another user's profile."
        }), 403

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
            "SELECT id, name, email, created_at FROM users WHERE id = %s",
            (auth_user_id,)
        )
        user = cursor.fetchone()

        if not user:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404

        if "created_at" in user and user["created_at"]:
            user["created_at"] = str(user["created_at"])

        return jsonify({
            "success": True,
            "user": user
        }), 200

    except Exception as e:
        print("Get profile error:", e)
        return jsonify({
            "success": False,
            "message": "Could not fetch profile"
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


@app.route("/api/users", methods=["GET"])
def get_users():
    """Fetch users directory. Protected: requires authentication token or Admin API key."""
    auth_data = get_authenticated_user()
    admin_key = os.environ.get("ADMIN_API_KEY", "").strip()
    request_key = request.headers.get("X-Admin-Key", "").strip()

    is_admin = bool(admin_key and request_key == admin_key)

    if not auth_data and not is_admin:
        return jsonify({
            "success": False,
            "message": "Authentication required to access user list."
        }), 401

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

        for u in users:
            if "created_at" in u and u["created_at"]:
                u["created_at"] = str(u["created_at"])

        return jsonify({
            "success": True,
            "users": users
        }), 200

    except Exception as e:
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


# -------------------------------------------------------------
# APPLICATION ENTRYPOINT
# -------------------------------------------------------------
if __name__ == "__main__":
    port_val = os.environ.get("PORT", "5000")
    try:
        port_num = int(port_val)
    except (ValueError, TypeError):
        port_num = 5000

    app.run(
        host="0.0.0.0",
        port=port_num,
        debug=False
    )