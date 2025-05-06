import sqlite3

# Connect to the SQLite database (it will create the database if it doesn't exist)
conn = sqlite3.connect('smart_budget.db')  # This creates/opens the smart_budget.db file in the current directory

# Create a cursor object to interact with the database
cursor = conn.cursor()

# Create the 'users' table to store user information
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    total_balance REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
''')

# Create the 'categories' table to store predefined categories for transactions (Income/Expense)
cursor.execute('''
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);
''')

# Create the 'transactions' table to store each user's income/expense transactions
cursor.execute('''
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT CHECK(type IN ('Income', 'Expense')),
    amount REAL NOT NULL,
    category_id INTEGER,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(category_id) REFERENCES categories(id)
);
''')

# Create the 'reports' table to store summarized reports for users
cursor.execute('''
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    total_income REAL DEFAULT 0,
    total_expense REAL DEFAULT 0,
    net_balance REAL DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
''')


# Commit the changes
conn.commit()

# Close the connection
conn.close()

print("Database and tables created successfully!")
