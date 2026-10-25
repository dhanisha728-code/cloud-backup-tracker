import os
import mysql.connector
from dotenv import load_dotenv

print("Step 1: Python is running")

load_dotenv()
print("Step 2: .env file loaded")

try:
    print("Step 3: Connecting to MySQL...")

    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        connection_timeout=5
    )

    print("Step 4: MySQL connected successfully!")

    cursor = connection.cursor()
    cursor.execute("SHOW TABLES")
    print("Tables:", cursor.fetchall())

    cursor.close()
    connection.close()

except Exception as error:
    print("ERROR:", error)