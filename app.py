from flask import Flask, render_template, request, redirect, send_from_directory, jsonify, session
import sqlite3
import os
from datetime import datetime, timedelta
import csv
from io import StringIO
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_database_path():
    custom_path = os.getenv("DATABASE_PATH")
    if custom_path:
        return custom_path

    if os.getenv("WEBSITE_INSTANCE_ID"):
        home_dir = os.getenv("HOME", "/home")
        data_dir = os.path.join(home_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        return os.path.join(data_dir, "expenses.db")

    return os.path.join(BASE_DIR, "expenses.db")


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "smartspend-secret-key-2026")

DATABASE = get_database_path()


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    
    # Create users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    # Create expenses table with user_id foreign key
    conn.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    # Create budgets table for monthly limit setting
    conn.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            budget_amount REAL NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(user_id, month),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    # Migration: add user_id to older databases created before auth was added
    expense_columns = [row['name'] for row in conn.execute('PRAGMA table_info(expenses)').fetchall()]
    if 'user_id' not in expense_columns:
        conn.execute('ALTER TABLE expenses ADD COLUMN user_id INTEGER')

        # Backfill legacy rows to first available user (if any)
        first_user = conn.execute('SELECT id FROM users ORDER BY id ASC LIMIT 1').fetchone()
        if first_user:
            conn.execute('UPDATE expenses SET user_id = ? WHERE user_id IS NULL', (first_user['id'],))
    
    conn.commit()
    conn.close()


init_db()


# Decorator to require login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')
        
        if len(password) < 6:
            return render_template('register.html', error='Password must be at least 6 characters')
        
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (username, email, password, created_at) VALUES (?, ?, ?, ?)',
                (username, email, generate_password_hash(password), datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
            return redirect('/login')
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('register.html', error='Username or email already exists')
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect('/')
        else:
            return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            return render_template('forgot_password.html', error='Passwords do not match')
        
        if len(new_password) < 6:
            return render_template('forgot_password.html', error='Password must be at least 6 characters')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if not user:
            conn.close()
            return render_template('forgot_password.html', error='Username not found')
        
        try:
            conn.execute(
                'UPDATE users SET password = ? WHERE id = ?',
                (generate_password_hash(new_password), user['id'])
            )
            conn.commit()
            conn.close()
            return render_template('forgot_password.html', success='Password reset successfully! You can now login with your new password.')
        except Exception as e:
            conn.close()
            return render_template('forgot_password.html', error='An error occurred. Please try again.')
    
    return render_template('forgot_password.html')


@app.route('/profile')
@login_required
def profile():
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('profile.html', user=user)


@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    email = request.form['email']
    current_password = request.form['current_password']
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if not check_password_hash(user['password'], current_password):
        conn.close()
        return render_template('profile.html', user=user, error='Current password is incorrect')
    
    if new_password:
        if new_password != confirm_password:
            conn.close()
            return render_template('profile.html', user=user, error='New passwords do not match')
        if len(new_password) < 6:
            conn.close()
            return render_template('profile.html', user=user, error='Password must be at least 6 characters')
        password_hash = generate_password_hash(new_password)
    else:
        password_hash = user['password']
    
    try:
        conn.execute(
            'UPDATE users SET email = ?, password = ? WHERE id = ?',
            (email, password_hash, session['user_id'])
        )
        conn.commit()
        conn.close()
        return render_template('profile.html', user={'id': user['id'], 'username': user['username'], 'email': email}, success='Profile updated successfully!')
    except sqlite3.IntegrityError:
        conn.close()
        return render_template('profile.html', user=user, error='Email already in use')


# Dashboard Route
@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    user_id = session['user_id']
    
    # Get all expenses for this user
    expenses = conn.execute('SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC', (user_id,)).fetchall()
    
    # Calculate total expense
    total_result = conn.execute('SELECT SUM(amount) as total FROM expenses WHERE user_id = ?', (user_id,)).fetchone()
    total_expense = total_result['total'] if total_result['total'] else 0
    
    # Get expense count
    count_result = conn.execute('SELECT COUNT(*) as count FROM expenses WHERE user_id = ?', (user_id,)).fetchone()
    expense_count = count_result['count']
    
    # Get recent expenses (last 5)
    recent_expenses = conn.execute('SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC LIMIT 5', (user_id,)).fetchall()
    
    # Get current month total
    current_month = datetime.now().strftime('%Y-%m')
    current_month_result = conn.execute(
        'SELECT SUM(amount) as total FROM expenses WHERE user_id = ? AND strftime("%Y-%m", date) = ?',
        (user_id, current_month)
    ).fetchone()
    current_month_total = current_month_result['total'] if current_month_result['total'] else 0

    # Get monthly budget
    budget_result = conn.execute(
        'SELECT budget_amount FROM budgets WHERE user_id = ? AND month = ?',
        (user_id, current_month)
    ).fetchone()
    monthly_budget = budget_result['budget_amount'] if budget_result else None

    budget_exceeded = monthly_budget is not None and current_month_total > monthly_budget
    budget_remaining = (monthly_budget - current_month_total) if monthly_budget is not None else None
    budget_exceeded_amount = (current_month_total - monthly_budget) if budget_exceeded else 0
    budget_usage_percent = 0
    if monthly_budget and monthly_budget > 0:
        budget_usage_percent = min((current_month_total / monthly_budget) * 100, 100)
    
    # Get category totals
    category_totals = conn.execute('''
        SELECT category, SUM(amount) as total 
        FROM expenses 
        WHERE user_id = ?
        GROUP BY category 
        ORDER BY total DESC
        LIMIT 5
    ''', (user_id,)).fetchall()
    
    # Get max category total for progress bar
    max_category_total = category_totals[0]['total'] if category_totals else 1
    
    conn.close()
    
    return render_template('index.html',
                         username=session['username'],
                         expenses=expenses,
                         total_expense=total_expense,
                         expense_count=expense_count,
                         recent_expenses=recent_expenses,
                         current_month_total=current_month_total,
                         monthly_budget=monthly_budget,
                         budget_exceeded=budget_exceeded,
                         budget_remaining=budget_remaining,
                         budget_exceeded_amount=budget_exceeded_amount,
                         budget_usage_percent=budget_usage_percent,
                         current_month=current_month,
                         category_totals=category_totals,
                         max_category_total=max_category_total)


# Set Monthly Budget Route
@app.route('/set-budget', methods=['POST'])
@login_required
def set_monthly_budget():
    user_id = session['user_id']
    budget_amount = request.form.get('budget_amount', '').strip()
    current_month = datetime.now().strftime('%Y-%m')

    if not budget_amount:
        return redirect('/')

    try:
        budget_value = float(budget_amount)
        if budget_value <= 0:
            return redirect('/')
    except ValueError:
        return redirect('/')

    conn = get_db_connection()
    now_iso = datetime.now().isoformat()
    conn.execute('''
        INSERT INTO budgets (user_id, month, budget_amount, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, month)
        DO UPDATE SET budget_amount = excluded.budget_amount,
                      updated_at = excluded.updated_at
    ''', (user_id, current_month, budget_value, now_iso, now_iso))
    conn.commit()
    conn.close()

    return redirect('/')

# Add Expense Page Route
@app.route('/add', methods=['GET'])
@login_required
def add_expense_page():
    return render_template('add_expense.html', username=session['username'])

# Add Expense Form Submission Route
@app.route('/add', methods=['POST'])
@login_required
def add_expense():
    amount = request.form['amount']
    category = request.form['category']
    description = request.form.get('description', '')
    date = request.form['date']
    user_id = session['user_id']
    
    conn = get_db_connection()
    conn.execute('INSERT INTO expenses (user_id, amount, category, description, date) VALUES (?, ?, ?, ?, ?)',
                 (user_id, amount, category, description, date))
    conn.commit()
    conn.close()
    
    return redirect('/expenses')

# Track Expenses Page Route
@app.route('/expenses')
@login_required
def expenses_page():
    conn = get_db_connection()
    user_id = session['user_id']
    
    # Get all expenses for this user
    expenses = conn.execute('SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC', (user_id,)).fetchall()
    
    # Calculate total expense
    total_result = conn.execute('SELECT SUM(amount) as total FROM expenses WHERE user_id = ?', (user_id,)).fetchone()
    total_expense = total_result['total'] if total_result['total'] else 0
    
    conn.close()
    
    return render_template('expenses.html', username=session['username'], expenses=expenses, total_expense=total_expense)

# Analytics Page Route
@app.route('/analytics')
@login_required
def analytics_page():
    conn = get_db_connection()
    user_id = session['user_id']
    
    # Get all expenses for this user
    expenses = conn.execute('SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC', (user_id,)).fetchall()
    
    # Calculate total expense
    total_result = conn.execute('SELECT SUM(amount) as total FROM expenses WHERE user_id = ?', (user_id,)).fetchone()
    total_expense = total_result['total'] if total_result['total'] else 0
    
    # Get expense count
    count_result = conn.execute('SELECT COUNT(*) as count FROM expenses WHERE user_id = ?', (user_id,)).fetchone()
    expense_count = count_result['count']
    
    # Calculate average expense
    average_expense = total_expense / expense_count if expense_count > 0 else 0
    
    # Get current month total
    current_month = datetime.now().strftime('%Y-%m')
    current_month_result = conn.execute(
        'SELECT SUM(amount) as total FROM expenses WHERE user_id = ? AND strftime("%Y-%m", date) = ?',
        (user_id, current_month)
    ).fetchone()
    current_month_total = current_month_result['total'] if current_month_result['total'] else 0

    # Get last month total for comparison
    last_month = (datetime.now().replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
    last_month_result = conn.execute(
        'SELECT SUM(amount) as total FROM expenses WHERE user_id = ? AND strftime("%Y-%m", date) = ?',
        (user_id, last_month)
    ).fetchone()
    last_month_total = last_month_result['total'] if last_month_result['total'] else 0

    # Monthly comparison (this month vs last month)
    monthly_change_amount = current_month_total - last_month_total
    if last_month_total > 0:
        monthly_change_percent = (monthly_change_amount / last_month_total) * 100
    else:
        monthly_change_percent = None

    if monthly_change_amount > 0:
        monthly_change_direction = 'up'
    elif monthly_change_amount < 0:
        monthly_change_direction = 'down'
    else:
        monthly_change_direction = 'steady'
    
    # Get category data for charts
    category_data = conn.execute('''
        SELECT category, SUM(amount) as total 
        FROM expenses 
        WHERE user_id = ?
        GROUP BY category 
        ORDER BY total DESC
    ''', (user_id,)).fetchall()
    
    # Get top category
    top_category = category_data[0]['category'] if category_data else 'N/A'
    
    # Get monthly data for trend chart
    monthly_data = conn.execute('''
        SELECT strftime('%Y-%m', date) as month, SUM(amount) as total 
        FROM expenses 
        WHERE user_id = ?
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month ASC
    ''', (user_id,)).fetchall()
    
    conn.close()
    
    # Convert to list of dicts for JavaScript
    category_data_list = [dict(row) for row in category_data]
    monthly_data_list = [dict(row) for row in monthly_data]
    
    return render_template('analytics.html',
                         username=session['username'],
                         expenses=expenses,
                         total_expense=total_expense,
                         average_expense=average_expense,
                         current_month_total=current_month_total,
                         last_month_total=last_month_total,
                         monthly_change_amount=monthly_change_amount,
                         monthly_change_percent=monthly_change_percent,
                         monthly_change_direction=monthly_change_direction,
                         top_category=top_category,
                         category_data=category_data_list,
                         monthly_data=monthly_data_list)

# Favicon Routes
@app.route('/favicon.png')
def favicon_png():
    return send_from_directory(BASE_DIR, 'favicon.png', mimetype='image/png')

@app.route('/favicon.svg')
def favicon_svg():
    return send_from_directory(BASE_DIR, 'favicon.svg', mimetype='image/svg+xml')

# Edit Expense Page Route (GET)
@app.route('/edit/<int:expense_id>', methods=['GET'])
@login_required
def edit_expense_page(expense_id):
    conn = get_db_connection()
    user_id = session['user_id']
    expense = conn.execute('SELECT * FROM expenses WHERE id = ? AND user_id = ?', (expense_id, user_id)).fetchone()
    conn.close()
    
    if not expense:
        return redirect('/expenses')
    
    return render_template('edit_expense.html', username=session['username'], expense=expense)

# Edit Expense Form Submission Route (POST)
@app.route('/edit/<int:expense_id>', methods=['POST'])
@login_required
def edit_expense(expense_id):
    amount = request.form['amount']
    category = request.form['category']
    description = request.form.get('description', '')
    date = request.form['date']
    user_id = session['user_id']
    
    conn = get_db_connection()
    # Only update if the expense belongs to the current user
    conn.execute('UPDATE expenses SET amount = ?, category = ?, description = ?, date = ? WHERE id = ? AND user_id = ?',
                 (amount, category, description, date, expense_id, user_id))
    conn.commit()
    conn.close()
    
    return redirect('/expenses')

# Delete Expense Route
@app.route('/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    user_id = session['user_id']
    conn = get_db_connection()
    # Only delete if the expense belongs to the current user
    conn.execute('DELETE FROM expenses WHERE id = ? AND user_id = ?', (expense_id, user_id))
    conn.commit()
    conn.close()
    
    return redirect('/expenses')

# Export to CSV Route
@app.route('/export')
@login_required
def export_csv():
    conn = get_db_connection()
    user_id = session['user_id']
    expenses = conn.execute('SELECT id, date, category, description, amount FROM expenses WHERE user_id = ? ORDER BY date DESC', (user_id,)).fetchall()
    conn.close()
    
    # Create CSV content
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Category', 'Description', 'Amount (₹)'])
    
    for expense in expenses:
        writer.writerow([expense['date'], expense['category'], expense['description'] or '', f"{expense['amount']:.2f}"])
    
    # Prepare response
    response_output = output.getvalue()
    from flask import make_response
    response = make_response(response_output)
    response.headers['Content-Disposition'] = 'attachment; filename=expenses.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
