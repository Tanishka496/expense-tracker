import sqlite3

conn = sqlite3.connect('expenses.db')
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", tables)

# Check expenses table schema
if tables:
    cursor.execute("PRAGMA table_info(expenses)")
    schema = cursor.fetchall()
    print("\nExpenses Table Schema:")
    for row in schema:
        print(row)
    
    # Check if there's any data
    cursor.execute("SELECT COUNT(*) FROM expenses")
    count = cursor.fetchone()[0]
    print(f"\nTotal expenses: {count}")
    
    # Show sample data if any
    if count > 0:
        cursor.execute("SELECT * FROM expenses LIMIT 5")
        print("\nSample data:")
        for row in cursor.fetchall():
            print(row)
else:
    print("No tables found!")

conn.close()
print("\nDatabase check complete - No errors found!")
