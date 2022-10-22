import json
import psycopg2
import pandas as pd

secrets = json.load(open("secrets.json"))
config = json.load(open("config.json"))

def get_conn():
    return psycopg2.connect(database='volunteers',
                            user=secrets['db_username'],
                            password=secrets['db_password'],
                            host='127.0.0.1',
                            port='5432')


def add_user_to_db(username, first, last):
    with get_conn() as con:
        cur = con.cursor()
        cur.execute(f"""INSERT INTO users (username, first, last)
                         VALUES ('{username}', '{first}', '{last}')
                         ON CONFLICT DO NOTHING""")


def read_schedule():
    with get_conn() as con:
        return pd.read_sql_query("SELECT * FROM schedule_view", con)


def add_role_to_db(state: dict):
    with get_conn() as con:
        cur = con.cursor()

        username = state['username']
        rolename = config['roles'][state['role']]['name']
        subrole = config['roles'][state['role']]['subroles'][state['subrole']]['name']
        datetime = state['date']

        cur.execute(f"""INSERT INTO schedule (username, rolename, subrole, datetime)
                        VALUES ('{username}', '{rolename}', '{subrole}', '{datetime}') """)
