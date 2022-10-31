import json
import pandas as pd
from sqlalchemy import create_engine

secrets = json.load(open("secrets.json"))
config = json.load(open("config.json"))

db_string = f"postgresql://{secrets['db_username']}:{secrets['db_password']}@127.0.0.1:5432/volunteers"
con = create_engine(db_string)


def add_user_to_db(username, first, last, chat_id):
    con.execute(f"""INSERT INTO users (username, first, last, chat_id)
                     VALUES ('{username}', '{first}', '{last}', {chat_id})
                     ON CONFLICT DO NOTHING""")


def read_schedule():
    return pd.read_sql_query("SELECT * FROM schedule_view", con)


def add_role_to_db(state: dict):
    username = state['username']
    rolename = config['roles'][state['role']]['name']
    subrole = config['roles'][state['role']]['subroles'][state['subrole']]['name']
    datetime = state['date']

    con.execute(f"""INSERT INTO schedule (username, rolename, subrole, datetime)
                    VALUES ('{username}', '{rolename}', '{subrole}', '{datetime}') """)


def get_nearest_unconfirmed_entries(deadline: str):
    return pd.read_sql_query(f"""
        SELECT id, username, chat_id, subrole, datetime
        FROM schedule
        JOIN users USING (username)
        WHERE status in ('unconfirmed', 'notification sent')
          AND rolename = 'ЧАТ'
          AND datetime - now() < '{deadline}'
          AND datetime - now() > '0 seconds'
    """, con)


def set_entry_status(id: int, status: str):
    con.execute(f"UPDATE schedule SET status='{status}' WHERE id={id}")


def get_chat_id(username: str):
    return pd.read_sql_query(f"SELECT chat_id FROM users WHERE username = '{username}'", con)['chat_id'].to_list()[0]


def get_role_info(id: int):
    return pd.read_sql_query(f"SELECT * FROM schedule WHERE id={id}", con).iloc[0]


def get_admins():
    return pd.read_sql_query("SELECT username FROM users WHERE is_admin", con)['username'].to_list()