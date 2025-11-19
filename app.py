from flask import Flask, render_template, request, redirect, session
import mysql.connector

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="elms"
)
cursor = db.cursor(dictionary=True)

# --- LOGIN ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        if user:
            session['user'] = user
            return redirect('/admin' if user['role'] == 'admin' else '/dashboard')
    return render_template('login.html')

# --- EMPLOYEE DASHBOARD ---
@app.route('/dashboard')
def dashboard():
    if 'user' not in session or session['user']['role'] != 'employee':
        return redirect('/')
    cursor.execute("SELECT * FROM leave_requests WHERE user_id=%s", (session['user']['id'],))
    leaves = cursor.fetchall()
    return render_template('dashboard.html', leaves=leaves)

# --- APPLY LEAVE ---
@app.route('/apply', methods=['GET', 'POST'])
def apply_leave():
    if 'user' not in session: return redirect('/')
    if request.method == 'POST':
        lt = request.form['leave_type']
        fd = request.form['from_date']
        td = request.form['to_date']
        rs = request.form['reason']
        cursor.execute("INSERT INTO leave_requests (user_id, leave_type, from_date, to_date, reason) VALUES (%s,%s,%s,%s,%s)",
                       (session['user']['id'], lt, fd, td, rs))
        db.commit()
        return redirect('/dashboard')
    return render_template('apply_leave.html')

# --- ADMIN PANEL ---
@app.route('/admin')
def admin_panel():
    if 'user' not in session or session['user']['role'] != 'admin':
        return redirect('/')
    cursor.execute("SELECT leave_requests.*, users.username FROM leave_requests JOIN users ON leave_requests.user_id = users.id")
    leaves = cursor.fetchall()
    return render_template('admin_panel.html', leaves=leaves)

@app.route('/update/<int:id>/<status>')
def update_leave(id, status):
    cursor.execute("UPDATE leave_requests SET status=%s WHERE id=%s", (status, id))
    db.commit()
    return redirect('/admin')

# --- REPORTS PAGE (ADMIN) ---
@app.route('/reports', methods=['GET', 'POST'])
def reports():
    if 'user' not in session or session['user']['role'] != 'admin':
        return redirect('/')
    
    query = "SELECT leave_requests.*, users.username FROM leave_requests JOIN users ON leave_requests.user_id = users.id"
    val = ()
    if request.method == 'POST':
        status = request.form['status']
        if status != 'All':
            query += " WHERE leave_requests.status = %s"
            val = (status,)
    cursor.execute(query, val)
    leaves = cursor.fetchall()
    return render_template('report.html', leaves=leaves)

# --- LOGOUT ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
