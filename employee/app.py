from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import re

app = Flask(__name__)
app.secret_key = 'TA8018A13'
DB = 'employees.db'

def init_db():
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()

        # Create employee table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            ID TEXT PRIMARY KEY,
            Name TEXT,
            Phone_no TEXT,
            Designation TEXT,
            Salary REAL
        )
        """)

        # Create user table for login
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
        """)

        # Add default admin user
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', 'admin123'))

        conn.commit()

def is_valid_input(name, phone, designation):
    return (
        re.fullmatch(r'[A-Za-z ]+', name) and
        re.fullmatch(r'\d{10}', phone) and
        re.fullmatch(r'[A-Za-z ]+', designation)
    )

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    search_query = request.args.get('q')
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        if search_query:
            cursor.execute("SELECT * FROM employees WHERE ID LIKE ? OR Name LIKE ?", (f'%{search_query}%', f'%{search_query}%'))
        else:
            cursor.execute("SELECT * FROM employees")
        employees = cursor.fetchall()
    return render_template('index.html', employees=employees, query=search_query)

@app.route('/add', methods=['GET', 'POST'])
def add_employee():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        emp_id = request.form['id']
        name = request.form['name']
        phone = request.form['phone']
        designation = request.form['designation']
        salary = float(request.form['salary'])

        if not is_valid_input(name, phone, designation):
            return "❌ Invalid input: Name/Designation must contain only letters and spaces. Phone must be 10 digits."

        try:
            with sqlite3.connect(DB) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO employees VALUES (?, ?, ?, ?, ?)", (emp_id, name, phone, designation, salary))
                conn.commit()
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            return "❌ Employee ID already exists!"
    return render_template('add.html')

@app.route('/update/<emp_id>', methods=['GET', 'POST'])
def update_employee(emp_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM employees WHERE ID = ?", (emp_id,))
        employee = cursor.fetchone()

    if request.method == 'POST':
        new_id = request.form['id']
        name = request.form['name']
        phone = request.form['phone']
        designation = request.form['designation']
        salary = float(request.form['salary'])

        if not is_valid_input(name, phone, designation):
            return "❌ Invalid input: Name/Designation must contain only letters and spaces. Phone must be 10 digits."

        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            if new_id != emp_id:
                cursor.execute("DELETE FROM employees WHERE ID = ?", (emp_id,))
            cursor.execute("INSERT OR REPLACE INTO employees VALUES (?, ?, ?, ?, ?)", (new_id, name, phone, designation, salary))
            conn.commit()
        return redirect(url_for('index'))

    return render_template('update.html', employee=employee)

@app.route('/delete/<emp_id>')
def delete_employee(emp_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    with sqlite3.connect(DB) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM employees WHERE ID = ?", (emp_id,))
        conn.commit()
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect(DB) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
            user = cursor.fetchone()
        if user:
            session['user'] = username
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials")
    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        new_password = request.form['new_password']

        conn = sqlite3.connect(DB)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if user:
            cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, username))
            conn.commit()
            flash("✅ Password reset successful. Please login.")
            return redirect(url_for('login'))
        else:
            flash("❌ Invalid username.")
        conn.close()

    return render_template('forgot_password.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)