from flask import Flask, render_template, request, flash, session, redirect, url_for  # Flask tools: app, pages, forms, messages, login session, redirects
from dotenv import load_dotenv  # reads secrets from the .env file
import os  # access environment variables
from hmac import compare_digest  # safe string comparison for passwords
from functools import wraps  # <-- 1. Needed for admin_required decorator  # keeps the original function's name when wrapping
from werkzeug.utils import secure_filename  # cleans filenames (imported but unused here)
from data import process_results  # your function that reads/cleans the CSV into a table
from save_to_db import save_results_to_db , get_db  # your functions: save data to DB, open DB connection

# --- STEP 1: SETUP APP ---
app = Flask(__name__)  # create your website
load_dotenv()  # load .env file

# secret key for session (login system needs this)
app.secret_key = os.getenv("SECRET_KEY")  # signs the session cookie so it can't be forged
password = os.getenv("PASSWORD")  # admin password from .env



# --- STEP 2: UPLOAD FOLDER CONFIG ---
# UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"csv"}  # only these file types may be uploaded
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB limit  # Flask rejects larger uploads automatically

def allowed_file(filename):  # checks if a filename has an allowed extension
    """Check if file is allowed (only csv)"""
    # needs a dot in the name, and the text after the last dot (lowercased) must be allowed
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --- STEP 3: SECURITY DECORATOR ---
# This is the guard that stops direct URL access
def admin_required(f):  # decorator: blocks a route unless admin is logged in
    @wraps(f)  # preserves the wrapped function's name and details
    def decorated_function(*args, **kwargs):  # runs in place of the protected route
        # check if admin is logged in (session exists)
        if not session.get("is_admin"):  # no admin flag in the session means not logged in
            flash("Please login first to access admin panel", "danger")  # show a red warning message
            return redirect(url_for('adminLogin'))  # send to login page
        return f(*args, **kwargs)  # logged in, so run the real route
    return decorated_function  # hand back the guarded version

# --- STEP 4: PUBLIC ROUTE ---
@app.route("/")  # URL: the home page
def home():  # shows the main portal page
    return render_template("portal.html")  # display the portal HTML

@app.route("/result")  # URL: /result?roll=123
def showResult():  # looks up and shows one student's result
    roll = request.args.get("roll")  # read the roll number from the URL

    if not roll:  # nothing was entered
        return render_template("index.html", error="Please enter Roll No")  # show page with an error

    conn = get_db()  # open the database connection
    cur = conn.cursor()  # cursor is used to run SQL queries

    # 1. Get student info from students table
    student = cur.execute(
        "SELECT * FROM students WHERE roll_no = ?", (roll,)  # "?" safely inserts roll (prevents SQL injection)
    ).fetchone()  # get just one matching row (or None)

    if not student:  # roll number doesn't exist
        conn.close()  # always close the connection
        return render_template("notFound.html", roll=roll)  # show "not found" page
    # 2. Get subject-wise marks from results + subjects tables
    results = cur.execute("""
        SELECT s.name as subject, r.marks 
        FROM results r
        JOIN subjects s ON r.subject_id = s.id
        WHERE r.roll_no = ?
        ORDER BY s.name
    """, (roll,)).fetchall()  # join marks with subject names, get all rows sorted by subject

    conn.close()  # done with the database

    # 3. Send both to HTML page
    return render_template("result.html", student=student, results=results)  # show the result page

# --- STEP 5: LOGIN ROUTE (PUBLIC) ---
@app.route('/login', methods=['GET', 'POST'])  # URL: /login, accepts page view and form submit
def adminLogin():  # shows login page and checks the password
    # if already logged in, go directly to admin panel
    if session.get("is_admin"):  # admin already logged in
        return redirect(url_for('adminDashboard'))  # skip login, go to dashboard
        
    if request.method == 'POST':  # form was submitted
       entered = request.form.get('password','')  # get typed password (empty if missing)
       # secure compare to prevent timing attacks
       if compare_digest(entered, password):  # password matches the one in .env
           session["is_admin"] = True  # remember the admin as logged in
           flash("Login successful!", "success")  # green success message
           return redirect(url_for('adminDashboard'))  # use redirect, not render_template
       # error message 
       flash("Incorrect password", "danger")  # wrong password, show red message

    return render_template('adminLogin.html')  # show the login form

# --- STEP 6: PROTECTED ADMIN ROUTES ---
# These routes CANNOT be accessed by typing URL directly

@app.route('/admin')  # URL: /admin
@admin_required  # <-- protection added here  # only logged-in admins get through
def adminDashboard():  # shows the admin main page
    """Main admin panel page"""
    return render_template("admin.html")  # display the admin HTML

@app.route("/admin/upload", methods=["POST"])  # URL: receives the uploaded file
@admin_required  # login required
def upload():  # validates the CSV and saves it to the database
    if "file" not in request.files:  # the form had no file field
        flash("No file selected", "danger")  # tell the admin
        return redirect(url_for('adminDashboard'))  # go back to the dashboard

    file = request.files["file"]  # get the uploaded file object

    if file.filename == "":  # file field exists but nothing was chosen
        flash("No file selected", "danger")  # tell the admin
        return redirect(url_for('adminDashboard'))  # go back to the dashboard

    if file and allowed_file(file.filename):  # file exists and is a .csv
        try:  # catch any errors during processing
            # NO file.save() - NO uploads folder - NO results.csv
            # Read directly from memory
            df = process_results(file)  # Pass the file object itself, not file.filename  # df = cleaned data table
            
            save_results_to_db(df)  # write all rows into the database
            
            flash(f"Success! {len(df)} students saved to database!", "success")  # show how many rows saved
        except Exception as e:  # something went wrong
            flash(f"Database error: {e}", "danger")  # show the error message

        return redirect(url_for('adminDashboard'))  # back to dashboard either way
    
    flash("Only .csv files allowed", "danger")  # wrong file type
    return redirect(url_for('adminDashboard')) 


    

# --- STEP 7: LOGOUT ROUTE ---
@app.route('/logout')  # URL: /logout
@admin_required  # must be logged in to log out
def logout():  # logs the admin out
    """Logout admin"""
    session.pop("is_admin", None)  # remove session  # delete the login flag (no error if missing)
    flash("Logged out successfully", "info")  # blue info message
    return redirect(url_for('adminLogin'))  # go to the login page

# --- STEP 8: RUN SERVER ---
if __name__ == '__main__':  # only run when this file is started directly
    app.run(debug=True)  # start server  # debug=True is for development only, turn off in production