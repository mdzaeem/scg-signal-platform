from db import get_connection

print("🔹 Running DB connection test...")

conn = get_connection()
cursor = conn.cursor()

cursor.execute("SELECT version();")
result = cursor.fetchone()

print("🔹 PostgreSQL Version:", result)

cursor.close()
conn.close()
