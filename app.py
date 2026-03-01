from flask import Flask, render_template, request, redirect
import sqlite3
import os

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


app = Flask(__name__, template_folder=BASE_DIR)

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

@app.route('/')
def index():
    conn = get_db_connection()
    expenses = conn.execute('SELECT * FROM expenses ORDER BY date DESC').fetchall()
    
    # Calculate total expense
    total_result = conn.execute('SELECT SUM(amount) as total FROM expenses').fetchone()
    total_expense = total_result['total'] if total_result['total'] else 0
    
    # Calculate monthly totals
    monthly_totals = conn.execute('''
        SELECT strftime('%Y-%m', date) as month, SUM(amount) as total 
        FROM expenses 
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month DESC
    ''').fetchall()
    
    conn.close()
    return render_template('index.html', expenses=expenses, total_expense=total_expense, monthly_totals=monthly_totals)

@app.route('/add', methods=['POST'])
def add_expense():
    amount = request.form['amount']
    category = request.form['category']
    description = request.form['description']
    date = request.form['date']
    
    conn = get_db_connection()
    conn.execute('INSERT INTO expenses (amount, category, description, date) VALUES (?, ?, ?, ?)',
                 (amount, category, description, date))
    conn.commit()
    conn.close()
    
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
