from flask import Flask, render_template, request, flash, session, redirect, url_for
from dotenv import load_dotenv
import os
from hmac import compare_digest
from functools import wraps  # <-- 1. Needed for admin_required decorator
from werkzeug.utils import secure_filename
from data import process_results
from save_to_db import save_results_to_db , get_db

# --- STEP 1: SETUP APP ---
app = Flask(__name__)  # create your website
load_dotenv()  # load .env file

# secret key for session (login system needs this)
app.secret_key = os.getenv("SECRET_KEY")
password = os.getenv("PASSWORD")  # admin password from .env



# --- STEP 2: UPLOAD FOLDER CONFIG ---
# UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"csv"}
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB limit

def allowed_file(filename):
    """Check if file is allowed (only csv)"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --- STEP 3: SECURITY DECORATOR ---
# This is the guard that stops direct URL access
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # check if admin is logged in (session exists)
        if not session.get("is_admin"):
            flash("Please login first to access admin panel", "danger")
            return redirect(url_for('adminLogin'))  # send to login page
        return f(*args, **kwargs)
    return decorated_function

# --- STEP 4: PUBLIC ROUTE ---
@app.route("/")
def home():
    return render_template("portal.html")

@app.route("/result")
def showResult():
    roll = request.args.get("roll")

    if not roll:
        return render_template("index.html", error="Please enter Roll No")

    conn = get_db()
    cur = conn.cursor()

    # 1. Get student info from students table
    student = cur.execute(
        "SELECT * FROM students WHERE roll_no = ?", (roll,)
    ).fetchone()

    if not student:
        conn.close()
        return render_template("notFound.html", roll=roll)
    # 2. Get subject-wise marks from results + subjects tables
    results = cur.execute("""
        SELECT s.name as subject, r.marks 
        FROM results r
        JOIN subjects s ON r.subject_id = s.id
        WHERE r.roll_no = ?
        ORDER BY s.name
    """, (roll,)).fetchall()

    conn.close()

    # 3. Send both to HTML page
    return render_template("result.html", student=student, results=results)

# --- STEP 5: LOGIN ROUTE (PUBLIC) ---
@app.route('/login', methods=['GET', 'POST'])
def adminLogin():
    # if already logged in, go directly to admin panel
    if session.get("is_admin"):
        return redirect(url_for('adminDashboard'))
        
    if request.method == 'POST':    
       entered = request.form.get('password','')
       # secure compare to prevent timing attacks
       if compare_digest(entered, password):
           session["is_admin"] = True
           flash("Login successful!", "success")
           return redirect(url_for('adminDashboard'))  # use redirect, not render_template
       # error message 
       flash("Incorrect password", "danger")

    return render_template('adminLogin.html')

# --- STEP 6: PROTECTED ADMIN ROUTES ---
# These routes CANNOT be accessed by typing URL directly

@app.route('/admin')
@admin_required  # <-- protection added here
def adminDashboard():
    """Main admin panel page"""
    return render_template("admin.html")

@app.route("/admin/upload", methods=["POST"])
@admin_required 
def upload():
    if "file" not in request.files:
        flash("No file selected", "danger")
        return redirect(url_for('adminDashboard'))

    file = request.files["file"]

    if file.filename == "":
        flash("No file selected", "danger")
        return redirect(url_for('adminDashboard'))

    if file and allowed_file(file.filename):
        try:
            # NO file.save() - NO uploads folder - NO results.csv
            # Read directly from memory
            df = process_results(file)  # Pass the file object itself, not file.filename
            
            save_results_to_db(df)
            
            flash(f"Success! {len(df)} students saved to database!", "success")
        except Exception as e:
            flash(f"Database error: {e}", "danger")

        return redirect(url_for('adminDashboard'))
    
    flash("Only .csv files allowed", "danger")
    return redirect(url_for('adminDashboard')) 


    

# --- STEP 7: LOGOUT ROUTE ---
@app.route('/logout')
@admin_required
def logout():
    """Logout admin"""
    session.pop("is_admin", None)  # remove session
    flash("Logged out successfully", "info")
    return redirect(url_for('adminLogin'))

# --- STEP 8: RUN SERVER ---
if __name__ == '__main__':
    app.run(debug=True)  # start server