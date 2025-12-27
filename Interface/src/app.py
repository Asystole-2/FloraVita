import os
import re
from flask import Flask, render_template, redirect, request, session, flash, url_for
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import google.generativeai as genai
from authlib.integrations.flask_client import OAuth
# os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

# Database Configuration
app.config.update(
    MYSQL_HOST=os.getenv("MYSQL_HOST"),
    MYSQL_USER=os.getenv("MYSQL_USER"),
    MYSQL_PASSWORD=os.getenv("MYSQL_PASSWORD", ""),
    MYSQL_DB='SmartIrrigation',
    MYSQL_CURSORCLASS="DictCursor"
)
mysql = MySQL(app)

# Configure Gemini AI
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("WARNING: GEMINI_API_KEY not found in .env file!")
genai.configure(api_key=api_key)
ai_model = genai.GenerativeModel('gemini-pro')

# OAuth Configuration for Google Login
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function

def is_valid_email(email):
    # Regex for standard email format validation
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)


# --- Authentication Routes ---
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

def password_complexity_check(password):
    """
    Returns a list of security requirements not met by the password.
    """
    errors = []
    if len(password) < 8:
        errors.append("Minimum 8 characters")
    if not re.search(r"[A-Z]", password):
        errors.append("One uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("One lowercase letter")
    if not re.search(r"\d", password):
        errors.append("One numeric digit")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("One special character")
    return errors

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Capture form data to return if validation fails
        form_data = {
            "username": request.form.get("username", "").strip(),
            "email": request.form.get("email", "").strip()
        }
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        #  Validation Logic
        if not is_valid_email(form_data["email"]):
            flash("Neural Link Error: Invalid email signature format.", "error")
            return render_template("register.html", **form_data)

        pw_errors = password_complexity_check(password)
        if pw_errors:
            error_msg = "Security Protocol Violation: " + ", ".join(pw_errors) + " required."
            flash(error_msg, "error")
            return render_template("register.html", **form_data)

        if password != confirm_password:
            flash("Synchronization Error: Passwords do not match.", "error")
            return render_template("register.html", **form_data)

        # Database Insertion and Automatic Login
        hashed_pw = generate_password_hash(password)
        cur = mysql.connection.cursor()
        try:
            # Insert the new user
            cur.execute("INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
                        (form_data["username"].lower(), form_data["email"].lower(), hashed_pw, 'user'))
            mysql.connection.commit()

            # Fetch the newly created user's ID to start the session
            cur.execute("SELECT id, username, role FROM users WHERE email = %s", (form_data["email"].lower(),))
            user = cur.fetchone()

            # Set session variables immediately
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            flash("Access Granted: Botanical profile synchronized and authorized.", "success")
            return redirect(url_for("dashboard"))

        except Exception:
            flash("Identity Conflict: Username or Email already in registry.", "error")
            return render_template("register.html", **form_data)
        finally:
            cur.close()

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = (request.form.get("identifier") or "").strip()
        password = (request.form.get("password") or "").strip()

        if not identifier or not password:
            flash("Please enter both credentials.", "error")
            return render_template("login.html")

        ident_lc = identifier.lower()
        cur = mysql.connection.cursor()
        try:
            if "@" in ident_lc:
                cur.execute("SELECT * FROM users WHERE LOWER(email)=%s LIMIT 1", (ident_lc,))
            else:
                cur.execute("SELECT * FROM users WHERE LOWER(username)=%s LIMIT 1", (ident_lc,))

            row = cur.fetchone()
            if not row or not check_password_hash(row["password"], password):
                flash("Incorrect credentials.", "error")
                return render_template("login.html")

            session["user_id"] = row["id"]
            session["username"] = row["username"]
            session["role"] = row["role"]
            return redirect(url_for("dashboard"))
        finally:
            cur.close()

    return render_template("login.html")


# Google Login OAuth Routes
@app.route('/login/google')
def google_login():
    redirect_uri = url_for('google_authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def google_authorize():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    if user_info:
        email = user_info['email']
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, username, role FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        if not user:
            # Create user if not exists (Oauth flow)
            username = email.split('@')[0]
            temp_pw = generate_password_hash(os.urandom(24).hex())
            cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                        (username, email, temp_pw))
            mysql.connection.commit()
            cur.execute("SELECT id, username, role FROM users WHERE email = %s", (email,))
            user = cur.fetchone()

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        cur.close()
        flash("Logged in with Google!", "success")
        return redirect(url_for("dashboard"))

    flash("Google authentication failed.", "error")
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("index"))


# --- Dashboard & Plant Management ---
@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session.get("user_id")
    cur = mysql.connection.cursor()
    cur.execute("""
                SELECT p.*, MAX(m.moisture_level) as last_moisture, MAX(m.recorded_at) as last_update
                FROM plants p
                         LEFT JOIN moisture_readings m ON p.id = m.plant_id
                WHERE p.user_id = %s
                GROUP BY p.id
                """, (user_id,))
    user_plants = cur.fetchall()
    cur.close()
    return render_template("dashboard.html", plants=user_plants, active_page="dashboard")

@app.route("/plant/<int:plant_id>")
@login_required
def plant_detail(plant_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM plants WHERE id = %s AND user_id = %s", (plant_id, session['user_id']))
    plant = cur.fetchone()

    if not plant:
        flash("Plant not found.", "error")
        return redirect(url_for('dashboard'))

    cur.execute("""
                SELECT moisture_level, recorded_at
                FROM moisture_readings
                WHERE plant_id = %s
                ORDER BY recorded_at DESC LIMIT 1
                """, (plant_id,))
    last_reading = cur.fetchone()
    cur.close()
    return render_template("plant_detail.html", plant=plant, last_reading=last_reading)

@app.route("/api/ai-tips/<int:plant_id>")
@login_required
def get_ai_tips(plant_id):
    # This route interfaces with the PlantCareAIAnalyzer class logic
    from Interface.src.ai_analyzer import PlantCareAIAnalyzer
    analyzer = PlantCareAIAnalyzer()

    cur = mysql.connection.cursor()
    cur.execute("""
                SELECT p.*, m.moisture_level as last_moisture
                FROM plants p
                         LEFT JOIN moisture_readings m ON p.id = m.plant_id
                WHERE p.id = %s
                  AND p.user_id = %s
                ORDER BY m.recorded_at DESC LIMIT 1
                """, (plant_id, session['user_id']))
    plant_data = cur.fetchone()
    cur.close()

    if not plant_data:
        return {"error": "Plant not found"}, 404

    return analyzer.get_care_advice(plant_data)

@app.route("/update-plant-photo/<int:plant_id>", methods=["POST"])
@login_required
def update_photo(plant_id):
    if 'photo' not in request.files: return redirect(url_for('dashboard'))
    file = request.files['photo']
    if file.filename == '': return redirect(url_for('dashboard'))

    filename = f"plant_{plant_id}.jpg"
    upload_path = os.path.join(app.root_path, 'static/uploads')
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)

    file.save(os.path.join(upload_path, filename))

    cur = mysql.connection.cursor()
    cur.execute("UPDATE plants SET image_url = %s WHERE id = %s AND user_id = %s",
                (filename, plant_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('dashboard'))


# --- System Routes ---
@app.route("/notifications")
@login_required
def notifications():
    user_id = session.get("user_id")
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM user_notifications WHERE user_id = %s ORDER BY created_at DESC LIMIT 50", (user_id,))
    user_notifications = cur.fetchall()
    cur.close()
    return render_template("notifications.html", active_page="notifications", notifications=user_notifications)


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user_id = session.get("user_id")
    cur = mysql.connection.cursor()

    # Pre-define hardware IDs (should be available for both GET and POST)
    available_devices = ["FV-NODE-001", "FV-NODE-002", "FV-NODE-003", "FV-NODE-004"]

    if request.method == "POST":
        new_username = request.form.get("username", "").lower().strip()
        new_email = request.form.get("email", "").lower().strip()
        new_password = request.form.get("new_password")
        current_password_verify = request.form.get("current_password_verify")

        # 1. Fetch current password for verification
        cur.execute("SELECT password FROM users WHERE id = %s", (user_id,))
        user_record = cur.fetchone()

        if not check_password_hash(user_record['password'], current_password_verify):
            flash("Security Violation: Identity verification failed.", "error")
        else:
            try:
                # 2. Update basic info
                cur.execute("UPDATE users SET username = %s, email = %s WHERE id = %s",
                            (new_username, new_email, user_id))

                # 3. Handle password update if provided
                if new_password:
                    pw_errors = password_complexity_check(new_password)
                    if pw_errors:
                        flash("Security Protocol: " + ", ".join(pw_errors), "error")
                        # We redirect here to clear POST data and show the flash
                        cur.close()
                        return redirect(url_for("settings"))

                    cur.execute("UPDATE users SET password = %s WHERE id = %s",
                                (generate_password_hash(new_password), user_id))

                mysql.connection.commit()
                session["username"] = new_username
                flash("Registry Synchronized: Profile updated successfully.", "success")
            except Exception:
                flash("Registry Conflict: Username or Email already exists.", "error")

        # After a POST, it is best practice to redirect to the same page (GET)
        # to prevent "Confirm Form Resubmission" on refresh.
        cur.close()
        return redirect(url_for("settings"))

    # --- GET REQUEST LOGIC ---
    # Fetch fresh user profile data to display in the form
    cur.execute("SELECT username, email FROM users WHERE id = %s", (user_id,))
    user_profile = cur.fetchone()
    cur.close()

    return render_template("settings.html",
                           user_profile=user_profile,
                           devices=available_devices,
                           active_page="settings")

@app.route("/delete-profile", methods=["POST"])
@login_required
def delete_profile():
    user_id = session.get("user_id")
    password_verify = request.form.get("delete_password_verify")

    cur = mysql.connection.cursor()
    cur.execute("SELECT password FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()

    if user and check_password_hash(user['password'], password_verify):
        try:
            # Delete related data first if not handled by ON DELETE CASCADE
            cur.execute("DELETE FROM moisture_readings WHERE plant_id IN (SELECT id FROM plants WHERE user_id = %s)",
                        (user_id,))
            cur.execute("DELETE FROM plants WHERE user_id = %s", (user_id,))
            cur.execute("DELETE FROM user_notifications WHERE user_id = %s", (user_id,))
            cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            mysql.connection.commit()
            session.clear()
            flash("Termination Complete: Profile and botanical data purged.", "success")
            return redirect(url_for("index"))
        except Exception as e:
            flash("System Error: Failed to purge data.", "error")
    else:
        flash("Security Violation: Incorrect password for account termination.", "error")

    cur.close()
    return redirect(url_for("settings"))

@app.route("/add-plant", methods=["POST"])
@login_required
def add_plant():
    name = request.form.get("plant_name")
    location = request.form.get("location")
    threshold = request.form.get("threshold", 30)
    user_id = session.get("user_id")

    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            INSERT INTO plants (name, location, moisture_threshold, user_id) 
            VALUES (%s, %s, %s, %s)
        """, (name, location, threshold, user_id))
        mysql.connection.commit()
        flash("Ecosystem Updated: New botanical device synchronized.", "success")
    except Exception as e:
        flash("Configuration Error: Could not register device.", "error")
    finally:
        cur.close()
    return redirect(url_for("settings"))

if __name__ == '__main__':
    app.run(debug=True)