import mysql.connector
import os
from os.path import join, dirname
from dotenv import load_dotenv

# Load environment variables from a .env file
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Retrieve database connection parameters from environment variables
db_name = os.getenv('db_name')
user_db = os.getenv('user')
pw_db = os.getenv('root_pw')
host = os.getenv('host')

# Establish a connection to the database
try:
    conn = mysql.connector.connect(
        host=host,
        database=db_name,
        user=user_db,
        password=pw_db,
        port=3306,
        ssl_disabled=True
    )
    c = conn.cursor(buffered=True)

    # Execute a simple query to keep the connection alive
    c.execute("SELECT 1")
    result = c.fetchone()
    print("Keep-alive query executed, result: ", result)

except mysql.connector.Error as error:
    print("Failed to keep alive MySQL connection: {}".format(error))

finally:
    # Close the cursor and the connection
    if conn.is_connected():
        c.close()
        conn.close()
        print("MySQL connection is closed")

