import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Sravani@2002",
    database="library_db"
)

cursor = db.cursor()