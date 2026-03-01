from flask import Flask, render_template, request, redirect, send_from_directory
import sqlite3
import os
from datetime import datetime

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

DATABASE = get_database_path()


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


init_db()

# Dashboard Route
@app.route('/')
def index():
    conn = get_db_connection()
    
    # Get all expenses
    expenses = conn.execute('SELECT * FROM expenses ORDER BY date DESC').fetchall()
    
    # Calculate total expense
    total_result = conn.execute('SELECT SUM(amount) as total FROM expenses').fetchone()
    total_expense = total_result['total'] if total_result['total'] else 0
    
    # Get expense count
    count_result = conn.execute('SELECT COUNT(*) as count FROM expenses').fetchone()
    expense_count = count_result['count']
    
    # Get recent expenses (last 5)
    recent_expenses = conn.execute('SELECT * FROM expenses ORDER BY date DESC LIMIT 5').fetchall()
    
    # Get current month total
    current_month = datetime.now().strftime('%Y-%m')
    current_month_result = conn.execute(
        'SELECT SUM(amount) as total FROM expenses WHERE strftime("%Y-%m", date) = ?',
        (current_month,)
    ).fetchone()
    current_month_total = current_month_result['total'] if current_month_result['total'] else 0
    
    # Get category totals
    category_totals = conn.execute('''
        SELECT category, SUM(amount) as total 
        FROM expenses 
        GROUP BY category 
        ORDER BY total DESC
        LIMIT 5
    ''').fetchall()
    
    # Get max category total for progress bar
    max_category_total = category_totals[0]['total'] if category_totals else 1
    
    conn.close()
    
    return render_template('index.html',
                         expenses=expenses,
                         total_expense=total_expense,
                         expense_count=expense_count,
                         recent_expenses=recent_expenses,
                         current_month_total=current_month_total,
                         category_totals=category_totals,
                         max_category_total=max_category_total)

# Add Expense Page Route
@app.route('/add', methods=['GET'])
def add_expense_page():
    return render_template('add_expense.html')

# Add Expense Form Submission Route
@app.route('/add', methods=['POST'])
def add_expense():
    amount = request.form['amount']
    category = request.form['category']
    description = request.form.get('description', '')
    date = request.form['date']
    
    conn = get_db_connection()
    conn.execute('INSERT INTO expenses (amount, category, description, date) VALUES (?, ?, ?, ?)',
                 (amount, category, description, date))
    conn.commit()
    conn.close()
    
    return redirect('/expenses')

# Track Expenses Page Route
@app.route('/expenses')
def expenses_page():
    conn = get_db_connection()
    
    # Get all expenses
    expenses = conn.execute('SELECT * FROM expenses ORDER BY date DESC').fetchall()
    
    # Calculate total expense
    total_result = conn.execute('SELECT SUM(amount) as total FROM expenses').fetchone()
    total_expense = total_result['total'] if total_result['total'] else 0
    
    conn.close()
    
    return render_template('expenses.html', expenses=expenses, total_expense=total_expense)

# Analytics Page Route
@app.route('/analytics')
def analytics_page():
    conn = get_db_connection()
    
    # Get all expenses
    expenses = conn.execute('SELECT * FROM expenses ORDER BY date DESC').fetchall()
    
    # Calculate total expense
    total_result = conn.execute('SELECT SUM(amount) as total FROM expenses').fetchone()
    total_expense = total_result['total'] if total_result['total'] else 0
    
    # Get expense count
    count_result = conn.execute('SELECT COUNT(*) as count FROM expenses').fetchone()
    expense_count = count_result['count']
    
    # Calculate average expense
    average_expense = total_expense / expense_count if expense_count > 0 else 0
    
    # Get current month total
    current_month = datetime.now().strftime('%Y-%m')
    current_month_result = conn.execute(
        'SELECT SUM(amount) as total FROM expenses WHERE strftime("%Y-%m", date) = ?',
        (current_month,)
    ).fetchone()
    current_month_total = current_month_result['total'] if current_month_result['total'] else 0
    
    # Get category data for charts
    category_data = conn.execute('''
        SELECT category, SUM(amount) as total 
        FROM expenses 
        GROUP BY category 
        ORDER BY total DESC
    ''').fetchall()
    
    # Get top category
    top_category = category_data[0]['category'] if category_data else 'N/A'
    
    # Get monthly data for trend chart
    monthly_data = conn.execute('''
        SELECT strftime('%Y-%m', date) as month, SUM(amount) as total 
        FROM expenses 
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month ASC
    ''').fetchall()
    
    conn.close()
    
    # Convert to list of dicts for JavaScript
    category_data_list = [dict(row) for row in category_data]
    monthly_data_list = [dict(row) for row in monthly_data]
    
    return render_template('analytics.html',
                         expenses=expenses,
                         total_expense=total_expense,
                         average_expense=average_expense,
                         current_month_total=current_month_total,
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

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
