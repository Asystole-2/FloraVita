import os
import re
import threading
import google
# from authlib.integrations.flask_client import OAuth
import pubnub
from flask import Flask, render_template, redirect, request, session, flash, url_for, jsonify
from flask_mysqldb import MySQL
from pubnub.callbacks import SubscribeCallback
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime, time

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

# PubNub Configuration for Moisture Data
pn_config = PNConfiguration()
pn_config.subscribe_key = os.getenv('PUBNUB_SUBSCRIBE_KEY')
pn_config.publish_key = os.getenv('PUBNUB_PUBLISH_KEY')
pn_config.user_id = "floravita_server"
pubnub = PubNub(pn_config)


class MoistureSubscriber(SubscribeCallback):
    def message(self, pubnub, message):
        """Handle incoming moisture data from sensors"""
        data = message.message
        hardware_id = data.get("hardware_id")
        moisture = data.get("moisture")
        status = data.get("status")

        print(f"Received moisture data: {hardware_id} - {moisture}%")

        # Use Flask application context
        with app.app_context():
            try:
                cur = mysql.connection.cursor()

                # Find which plant this hardware belongs to
                cur.execute("SELECT id FROM plants WHERE hardware_id = %s", (hardware_id,))
                plant = cur.fetchone()

                if plant:
                    plant_id = plant['id']

                    # Insert moisture reading
                    cur.execute("""
                                INSERT INTO moisture_readings (plant_id, moisture_level, pump_status, is_automated)
                                VALUES (%s, %s, FALSE, FALSE)
                                """, (plant_id, moisture))

                    # Update plant's last moisture
                    cur.execute("""
                                UPDATE plants
                                SET last_moisture = %s,
                                    last_update   = NOW()
                                WHERE id = %s
                                """, (moisture, plant_id))

                    mysql.connection.commit()
                    print(f"Updated plant {plant_id} with moisture {moisture}%")
                else:
                    print(f"No plant found with hardware_id: {hardware_id}")

                cur.close()
            except Exception as e:
                print(f"Error updating moisture data: {e}")
                try:
                    mysql.connection.rollback()
                except:
                    pass

    def status(self, pubnub, status):
        if status.category == "PNConnectedCategory":
            print("PubNub Connected - Listening for moisture data")

    def presence(self, pubnub, presence):
        pass

# Start PubNub listener in background thread
def start_pubnub_listener():
    """Start PubNub subscription in background thread"""
    try:
        listener = MoistureSubscriber()
        pubnub.add_listener(listener)
        pubnub.subscribe().channels("moisture-data").execute()
        print("Moisture data listener started")
    except Exception as e:
        print(f"Error starting PubNub listener: {e}")


# Start the listener when Flask starts
with app.app_context():
    try:
        # Run in a separate thread to not block Flask
        thread = threading.Thread(target=start_pubnub_listener, daemon=True)
        thread.start()
        time.sleep(1)  # Give it a moment to connect
    except Exception as e:
        print(f"Could not start PubNub listener: {e}")

# Configure Gemini AI
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("WARNING: GEMINI_API_KEY not found in .env file!")
genai.configure(api_key=api_key)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

# OAuth Configuration for Google Login
# google = oauth.register(
#     name='google',
#     client_id=os.getenv("GOOGLE_CLIENT_ID"),
#     client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
#     server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
#     client_kwargs={'scope': 'openid email profile'}
# )


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


# --- Notification Helper & Context Processor ---

def create_notification(user_id, plant_id, title, message, event_type):
    """Inserts a new notification and marks it as unread."""
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
                    INSERT INTO user_notifications (user_id, plant_id, title, message, event_type, is_read)
                    VALUES (%s, %s, %s, %s, %s, FALSE)
                    """, (user_id, plant_id, title, message, event_type))
        mysql.connection.commit()
    finally:
        cur.close()


@app.context_processor
def inject_notifications():
    """Provides unread notification count to all templates globally."""
    if "user_id" in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) as count FROM user_notifications WHERE user_id = %s AND is_read = FALSE",
                    (session['user_id'],))
        result = cur.fetchone()
        cur.close()
        return dict(unread_count=result['count'] if result else 0)
    return dict(unread_count=0)


# --- Routes ---

@app.route("/notifications")
@login_required
def notifications():
    user_id = session.get("user_id")
    cur = mysql.connection.cursor()
    try:
        # Fetch the 50 most recent notifications without changing their read status
        cur.execute("""
                    SELECT n.*, p.name as plant_name
                    FROM user_notifications n
                             LEFT JOIN plants p ON n.plant_id = p.id
                    WHERE n.user_id = %s
                    ORDER BY n.created_at DESC LIMIT 50
                    """, (user_id,))
        user_notifications = cur.fetchall()

        return render_template("notifications.html",
                               active_page="notifications",
                               notifications=user_notifications)
    finally:
        cur.close()


@app.route("/api/unread-count")
@login_required
def get_unread_count():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) as count FROM user_notifications WHERE user_id = %s AND is_read = FALSE",
                (session['user_id'],))
    result = cur.fetchone()
    cur.close()
    return {"count": result['count'] if result else 0}


# --- Notification Management Routes ---

@app.route("/notifications/mark-read/<int:note_id>", methods=["POST"])
@login_required
def mark_notification_read(note_id):
    cur = None
    try:
        cur = mysql.connection.cursor()
        cur.execute("UPDATE user_notifications SET is_read = TRUE WHERE id = %s AND user_id = %s",
                    (note_id, session['user_id']))
        mysql.connection.commit()
        return {"status": "success", "message": "Notification marked as read", "note_id": note_id}
    except Exception as e:
        print(f"Error in mark_notification_read: {str(e)}")
        mysql.connection.rollback()
        return {"status": "error", "message": str(e)}, 500
    finally:
        if cur:
            cur.close()


@app.route("/notifications/mark-unread/<int:note_id>", methods=["POST"])
@login_required
def mark_notification_unread(note_id):
    cur = None
    try:
        cur = mysql.connection.cursor()
        cur.execute("UPDATE user_notifications SET is_read = FALSE WHERE id = %s AND user_id = %s",
                    (note_id, session['user_id']))
        mysql.connection.commit()
        return {"status": "success", "message": "Notification marked as unread", "note_id": note_id}
    except Exception as e:
        print(f"Error in mark_notification_unread: {str(e)}")
        mysql.connection.rollback()
        return {"status": "error", "message": str(e)}, 500
    finally:
        if cur:
            cur.close()


@app.route("/notifications/mark-all-read", methods=["POST"])
@login_required
def mark_all_notifications_read():
    cur = None
    try:
        cur = mysql.connection.cursor()
        cur.execute("UPDATE user_notifications SET is_read = TRUE WHERE user_id = %s", (session['user_id'],))
        mysql.connection.commit()

        # Get count of updated notifications
        cur.execute("SELECT COUNT(*) as count FROM user_notifications WHERE user_id = %s", (session['user_id'],))
        count = cur.fetchone()['count']

        return {"status": "success", "message": f"All notifications marked as read", "count": count}
    except Exception as e:
        print(f"Error in mark_all_notifications_read: {str(e)}")
        mysql.connection.rollback()
        return {"status": "error", "message": str(e)}, 500
    finally:
        if cur:
            cur.close()


@app.route("/notifications/delete/<int:note_id>", methods=["POST"])
@login_required
def delete_notification(note_id):
    cur = None
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM user_notifications WHERE id = %s AND user_id = %s", (note_id, session['user_id']))
        mysql.connection.commit()
        return {"status": "success", "message": "Notification deleted", "note_id": note_id}
    except Exception as e:
        print(f"Error in delete_notification: {str(e)}")
        mysql.connection.rollback()
        return {"status": "error", "message": str(e)}, 500
    finally:
        if cur:
            cur.close()


@app.route("/notifications/delete-bulk", methods=["POST"])
@login_required
def delete_notifications_bulk():
    cur = None
    try:
        ids = request.form.getlist('notification_ids')
        if not ids:
            return {"status": "error", "message": "No notification IDs provided"}, 400

        cur = mysql.connection.cursor()
        format_strings = ','.join(['%s'] * len(ids))
        cur.execute(f"DELETE FROM user_notifications WHERE id IN ({format_strings}) AND user_id = %s",
                    tuple(ids) + (session['user_id'],))
        mysql.connection.commit()
        return {"status": "success", "message": f"Successfully deleted {len(ids)} notifications", "count": len(ids)}
    except Exception as e:
        print(f"Error in delete_notifications_bulk: {str(e)}")
        mysql.connection.rollback()
        return {"status": "error", "message": str(e)}, 500
    finally:
        if cur:
            cur.close()


@app.route("/notifications/mark-bulk-read", methods=["POST"])
@login_required
def mark_notifications_bulk_read():
    cur = None
    try:
        # Support both JSON and form data
        if request.is_json:
            data = request.get_json()
            if not data:
                return {"status": "error", "message": "No data provided"}, 400
            ids = data.get('notification_ids', [])
        else:
            ids = request.form.getlist('notification_ids')

        if not ids:
            return {"status": "error", "message": "No notification IDs provided"}, 400

        cur = mysql.connection.cursor()
        placeholders = ','.join(['%s'] * len(ids))
        query = f"UPDATE user_notifications SET is_read = TRUE WHERE id IN ({placeholders}) AND user_id = %s"
        params = tuple(ids) + (session['user_id'],)

        cur.execute(query, params)
        mysql.connection.commit()
        return {"status": "success", "message": f"Marked {len(ids)} notifications as read", "count": len(ids)}
    except Exception as e:
        print(f"Error in mark_notifications_bulk_read: {str(e)}")
        mysql.connection.rollback()
        return {"status": "error", "message": str(e)}, 500
    finally:
        if cur:
            cur.close()


@app.route("/notifications/mark-bulk-unread", methods=["POST"])
@login_required
def mark_notifications_bulk_unread():
    cur = None
    try:
        # Support both JSON and form data
        if request.is_json:
            data = request.get_json()
            if not data:
                return {"status": "error", "message": "No data provided"}, 400
            ids = data.get('notification_ids', [])
        else:
            ids = request.form.getlist('notification_ids')

        if not ids:
            return {"status": "error", "message": "No notification IDs provided"}, 400

        cur = mysql.connection.cursor()
        format_strings = ','.join(['%s'] * len(ids))
        cur.execute(f"UPDATE user_notifications SET is_read = FALSE WHERE id IN ({format_strings}) AND user_id = %s",
                    tuple(ids) + (session['user_id'],))
        mysql.connection.commit()
        return {"status": "success", "message": f"Marked {len(ids)} notifications as unread", "count": len(ids)}
    except Exception as e:
        print(f"Error in mark_notifications_bulk_unread: {str(e)}")
        mysql.connection.rollback()
        return {"status": "error", "message": str(e)}, 500
    finally:
        if cur:
            cur.close()


@app.route("/notifications/delete-all", methods=["POST"])
@login_required
def delete_all_notifications():
    cur = None
    try:
        cur = mysql.connection.cursor()
        # Get count before deletion for message
        cur.execute("SELECT COUNT(*) as count FROM user_notifications WHERE user_id = %s", (session['user_id'],))
        count_result = cur.fetchone()
        count = count_result['count'] if count_result else 0

        # Delete all notifications
        cur.execute("DELETE FROM user_notifications WHERE user_id = %s", (session['user_id'],))
        mysql.connection.commit()
        return {"status": "success", "message": f"Deleted all notifications", "count": count}
    except Exception as e:
        print(f"Error in delete_all_notifications: {str(e)}")
        mysql.connection.rollback()
        return {"status": "error", "message": str(e)}, 500
    finally:
        if cur:
            cur.close()

@app.route("/update-threshold/<int:plant_id>", methods=["POST"])
@login_required
def update_threshold(plant_id):
    data = request.get_json()
    new_threshold = data.get("threshold")
    cur = mysql.connection.cursor()
    try:
        cur.execute("UPDATE plants SET moisture_threshold = %s WHERE id = %s AND user_id = %s",
                    (new_threshold, plant_id, session['user_id']))
        mysql.connection.commit()

        # Trigger notification for threshold change
        create_notification(
            session['user_id'], plant_id, "Threshold Updated",
            f"Moisture threshold set to {new_threshold}% on {datetime.now().strftime('%Y-%m-%d %H:%M')}.",
            'threshold_update'
        )
        return {"status": "success", "threshold": new_threshold}
    finally:
        cur.close()

@app.route("/toggle-pump/<int:plant_id>", methods=["POST"])
@login_required
def toggle_pump(plant_id):
    data = request.get_json()
    is_active = data.get('active', False)  # Determine if starting or stopping

    cur = mysql.connection.cursor()
    try:
        # 1. Authorization Check
        cur.execute("SELECT name FROM plants WHERE id = %s AND user_id = %s", (plant_id, session['user_id']))
        plant = cur.fetchone()

        if not plant:
            return {"status": "error", "message": "Unauthorized"}, 404

        # 2. Hardware Command (PubNub)
        # Sends real-time instruction to the Raspberry Pi subscriber
        command = "PUMP_ON" if is_active else "PUMP_OFF"
        pubnub.publish().channel("pump-commands").message({
            "command": command,
            "plant_id": plant_id,
            "timestamp": datetime.now().isoformat()
        }).sync()

        # Notification Logic
        if is_active:
            title = "Manual Watering"
            message = f"Irrigation for {plant['name']} triggered manually at {datetime.now().strftime('%H:%M')}."
            event_type = 'manual_watering'
        else:
            title = "Pump Deactivated"
            message = f"Manual irrigation for {plant['name']} was stopped at {datetime.now().strftime('%H:%M')}."
            event_type = 'system'

        create_notification(session['user_id'], plant_id, title, message, event_type)

        # Database Persistence
        # Logs the state change so the UI charts reflect the activity
        cur.execute("""
                    INSERT INTO moisture_readings (plant_id, pump_status, is_automated)
                    VALUES (%s, %s, FALSE)
                    """, (plant_id, is_active))

        mysql.connection.commit()
        return {"status": "success"}

    except Exception as e:
        mysql.connection.rollback()
        return {"status": "error", "message": str(e)}, 500
    finally:
        cur.close()


# --- Dashboard & Plant Management ---
@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session.get("user_id")
    cur = mysql.connection.cursor()

    try:
        # Get plants with their latest moisture readings
        cur.execute("""
                    SELECT p.*,
                           COALESCE(
                                   (SELECT m.moisture_level
                                    FROM moisture_readings m
                                    WHERE m.plant_id = p.id
                                    ORDER BY m.recorded_at DESC
                                   LIMIT 1), 
                    0
                )                                           as last_moisture,
                           COALESCE(
                                   (SELECT m.recorded_at
                                    FROM moisture_readings m
                                    WHERE m.plant_id = p.id
                                    ORDER BY m.recorded_at DESC
                                   LIMIT 1), 
                    p.created_at
                ) as last_update
                    FROM plants p
                    WHERE p.user_id = %s
                    ORDER BY p.id
                    """, (user_id,))

        user_plants = cur.fetchall()
        cur.close()

        # Debug output
        print(f"Dashboard: Found {len(user_plants)} plants for user {user_id}")
        for plant in user_plants:
            print(f"  - {plant['name']}: {plant['last_moisture']}% (updated: {plant['last_update']})")

        return render_template("dashboard.html", plants=user_plants, active_page="dashboard")

    except Exception as e:
        print(f"❌ Error in dashboard route: {e}")
        flash("Error loading dashboard", "error")
        return redirect(url_for("index"))


@app.route("/api/latest-moisture")
@login_required
def get_latest_moisture():
    """Get latest moisture readings for all user's plants"""
    user_id = session.get("user_id")
    cur = mysql.connection.cursor()

    try:
        # Get plants with their latest moisture data
        cur.execute("""
                    SELECT p.id                         as plant_id,
                           p.name,
                           COALESCE(p.last_moisture, 0) as moisture,
                           p.last_update as timestamp
                    FROM plants p
                    WHERE p.user_id = %s
                    ORDER BY p.id
                    """, (user_id,))

        updates = cur.fetchall()

        return jsonify({
            "success": True,
            "updates": [
                {
                    "plant_id": row['plant_id'],
                    "moisture": float(row['moisture']),
                    "timestamp": row['timestamp'].isoformat() if row['timestamp'] else None,
                    "plant_name": row['name']
                }
                for row in updates
            ]
        })
    except Exception as e:
        print(f"Error in get_latest_moisture: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cur.close()

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


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user_id = session.get("user_id")
    cur = mysql.connection.cursor()

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
    hardware_id = request.form.get("hardware_id")
    user_id = session.get("user_id")

    cur = mysql.connection.cursor()
    try:
        cur.execute("""
                    INSERT INTO plants (name, location, moisture_threshold, user_id, hardware_id)
                    VALUES (%s, %s, %s, %s, %s)
                    """, (name, location, threshold, user_id, hardware_id))
        mysql.connection.commit()
        flash("Ecosystem Updated: New botanical device synchronized.", "success")
    except Exception as e:
        flash("Configuration Error: Could not register device.", "error")
    finally:
        cur.close()
    return redirect(url_for("settings"))

@app.route("/remove-plant-photo/<int:plant_id>", methods=["POST"])
@login_required
def remove_photo(plant_id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE plants SET image_url = 'default_plant.png' WHERE id = %s AND user_id = %s",
                (plant_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    flash("Photo removed successfully.", "success")
    return redirect(url_for('dashboard'))


@app.route("/delete-plant/<int:plant_id>", methods=["POST"])
@login_required
def delete_plant(plant_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM plants WHERE id = %s AND user_id = %s", (plant_id, session['user_id']))
    mysql.connection.commit()
    cur.close()
    flash("Plant removed from your garden.", "success")
    return redirect(url_for('dashboard'))


@app.route("/update-plant-info/<int:plant_id>", methods=["POST"])
@login_required
def update_plant_info(plant_id):
    data = request.get_json()
    new_name = data.get("name")
    new_location = data.get("location")

    cur = mysql.connection.cursor()
    try:
        cur.execute("""
                    UPDATE plants
                    SET name     = %s,
                        location = %s
                    WHERE id = %s
                      AND user_id = %s
                    """, (new_name, new_location, plant_id, session['user_id']))
        mysql.connection.commit()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500
    finally:
        cur.close()


if __name__ == '__main__':
    app.run(debug=True)
