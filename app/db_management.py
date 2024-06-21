import mysql.connector
import os
import time
# from os.path import join, dirname
# from dotenv import load_dotenv
# dotenv_path = join(dirname(__file__), '../.env')
# load_dotenv(dotenv_path)

# database and user have to be created first of all
db_name = os.getenv('db_name')
user_db = os.getenv('user')
pw_db = db_password = os.getenv('root_pw')
host = os.getenv('host')


conn = mysql.connector.connect(host=host, user=user_db, password=pw_db, port = 3306, ssl_disabled = True)
c = conn.cursor(buffered=True)
c.execute('CREATE DATABASE IF NOT EXISTS %s CHARACTER SET utf8 COLLATE utf8_bin;' % db_name)

#c.execute('DROP DATABASE data;')

# db_connection = None
# db_cursor = None

def get_connection():
    # global db_connection
    # if db_connection is None:
    #     db_connection = mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('root_pw'), database=os.getenv('db_name'), port = 3306, ssl_disabled = True)
    return mysql.connector.connect(host=os.getenv('host'), user=os.getenv('user'), password=os.getenv('root_pw'), database=os.getenv('db_name'), port = 3306, ssl_disabled = True)
def get_cursor():
    # global db_cursor
    db_connection = get_connection()
    # if db_cursor is None:
    #     db_cursor = get_connection().cursor(buffered=True)
    return (db_connection, db_connection.cursor(buffered=True))

# def reset_connection():
#     global db_connection
#     global db_cursor
#     db_connection = get_connection()
#     db_cursor = get_cursor()


# reset_connection()


def execute(query, values=None, commit=False,retry=0):
    max_retries = 5
    db_connection, db_cursor = get_cursor()
    try:
        if values is None:
            db_cursor.execute(query)
        else:
            db_cursor.execute(query, values)
        if commit:
            db_connection.commit()
    except Exception as e:
        if retry < max_retries:
            time.sleep(1)
            execute(query, values, commit, retry+1)
        else:
            raise e
    finally:
        db_connection.close()


def execute_fetch_all(query, values=None, retry=0):
    max_retries = 5
    db_connection, db_cursor = get_cursor()
    try:
        if values is None:
            db_cursor.execute(query)
        else:
            db_cursor.execute(query, values)
        return db_cursor.fetchall()
    except Exception as e:
        # reset_connection()
        if retry < max_retries:
            time.sleep(5)
            execute_fetch_all(query, values, retry+1)
        else:
            raise e
    finally:
        db_connection.close()

# create tables
def create_usertable():
    execute('CREATE TABLE IF NOT EXISTS userstable(user VARCHAR(100) PRIMARY KEY,password TEXT);')


def create_qandatable():
    execute(
        'CREATE TABLE IF NOT EXISTS qandatable(rowid INTEGER auto_increment PRIMARY KEY,user VARCHAR(100), message TEXT, role VARCHAR(100), FOREIGN KEY (user) REFERENCES userstable(user));')

def create_knowledgebases_private():
    execute(
        'CREATE TABLE IF NOT EXISTS knowledgebases_private(rowid INTEGER auto_increment PRIMARY KEY,user VARCHAR(100), knowledgebase VARCHAR(100), FOREIGN KEY (user) REFERENCES userstable(user));')

def create_knowledgebases_public():
    execute(
        'CREATE TABLE IF NOT EXISTS knowledgebases_public(rowid INTEGER auto_increment PRIMARY KEY, knowledgebase VARCHAR(100), protected boolean);')
    #add protected database
    if check_if_public_knowledgebase_already_exists("index_repo4euD21openaccess"):
        add_public_knowledgebase("index_repo4euD21openaccess", True)

def delete_qanda(user):
    execute('DELETE FROM qandatable WHERE user = %s;', [user], commit=True)

def delete_private_knowledgebase(user, knowledgebase):
    execute('DELETE FROM knowledgebases_private WHERE user = %s AND knowledgebase = %s;', (user, knowledgebase), commit=True)

def delete_public_knowledgebase(knowledgebase):
    execute('DELETE FROM knowledgebases_public WHERE knowledgebase = %s;', [knowledgebase], commit=True)


def add_qandadata(username, message, role):
    execute('INSERT INTO qandatable(user,message, role) VALUES (%s, %s, %s);', (username, message, role), commit=True)


def add_userdata(username, password):
    execute('INSERT INTO userstable(user,password) VALUES (%s, %s);', (username, password), commit =True)

def add_private_knowledgebase(username, knowledgebase):
    execute('INSERT INTO knowledgebases_private(user,knowledgebase) VALUES (%s, %s);', (username, knowledgebase), commit=True)

def get_private_knowledgebase(username):
    return execute_fetch_all('SELECT * FROM knowledgebases_private WHERE user = %s;', [username])

def add_public_knowledgebase(knowledgebase, protected):
    execute('INSERT INTO knowledgebases_public(knowledgebase, protected) VALUES (%s, %s);', (knowledgebase, protected), commit=True)

def get_public_knowledgebase():
    return execute_fetch_all('SELECT * FROM knowledgebases_public')


def get_qandadata(username):
    return execute_fetch_all('SELECT * FROM qandatable WHERE user = %s;', [username])


def get_user_data(username):
    return execute_fetch_all('SELECT * FROM userstable WHERE user = %s;', [username])


def check_if_user_already_exists(username):
    return len(execute_fetch_all('SELECT * FROM userstable WHERE user = %s;', [username])) == 0


def login_user(username, password):
    return execute_fetch_all('SELECT * FROM userstable WHERE user = %s AND password = %s ;', (username, password))

def check_if_public_knowledgebase_already_exists(knowledgebase):
    return len(execute_fetch_all('SELECT * FROM knowledgebases_public WHERE knowledgebase = %s;', [knowledgebase])) == 0

def check_if_public_knowledgebase_protected(knowledgebase):
    data = execute_fetch_all('SELECT * FROM knowledgebases_public WHERE knowledgebase = %s;', [knowledgebase])
    if len(data) == 0:
        #private database -> is not protected
        print("not protected")
        return False
    return data[0][2]