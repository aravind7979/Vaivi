import sqlite3
conn = sqlite3.connect('vaivi.db')
columns = conn.cursor().execute('PRAGMA table_info(users)').fetchall()
with open('cols.txt', 'w') as f:
    for col in columns:
        f.write(f"{col[0]} | {col[1]} | {col[2]}\n")
