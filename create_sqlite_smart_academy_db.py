import sqlite3

db_path = "smart_academy.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create `users` table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    firstname TEXT NOT NULL,
    lastname TEXT NOT NULL,
    phone TEXT,
    email TEXT UNIQUE NOT NULL,
    face_signature BLOB,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
""")

# Create `interests` table
cursor.execute("""
CREATE TABLE IF NOT EXISTS interests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    interest TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
""")

conn.commit()

# Close the database connection
conn.close()


