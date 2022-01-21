from pathlib import Path
from contextlib import closing
import sqlite3
from flask import g
import os.path


PROFILE_DIR = os.environ["FIREFOX_PROFILE_DIR"]
DATABASE = os.path.join(PROFILE_DIR, "whatsapp_api_service.sqlite3")


def get_conn():
    db = None
    if bool(g):
        db = getattr(g, '_database', None)

    if db is None:
        db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row

    if bool(g):
        g._database = db

    return db


def get_user_by_token(token):
    with closing(get_conn().cursor()) as cr:
        cr.execute("SELECT * FROM users WHERE token = ? LIMIT 1", [token])
        return cr.fetchone()


def get_user_by_id(user_id):
    with closing(get_conn().cursor()) as cr:
        cr.execute("SELECT * FROM users WHERE id = ? LIMIT 1", [user_id])
        return cr.fetchone()


def get_all_users():
    with closing(get_conn().cursor()) as cr:
        r = []
        path = Path(PROFILE_DIR)
        for child in path.iterdir():
            if "." not in child.name:  # firefox profile format is "randomstring.profile_name"
                continue

            if child.is_dir():
                # FIXME: too many queries on database
                cr.execute("SELECT * FROM users where name = ? LIMIT 1", [child.name])
                row = cr.fetchone()
                if row:
                    r.append(row)
                else:
                    r.append({"id": None, "name": child.name, "token": None, "webhook_url": None})
        return r


def create_user(name, token):
    conn = get_conn()
    with closing(conn.cursor()) as cr:
        cr.execute("INSERT INTO users(name, token) VALUES (?, ?)", [name, token])
        conn.commit()
        return cr.fetchone()


def get_all_webhooks():
    with closing(get_conn().cursor()) as cr:
        cr.execute("SELECT id AS user_id, name AS user_name, webhook_url FROM users", [])
        return cr.fetchall()


def set_webhook_url(user_id, webhook_url):
    conn = get_conn()
    with closing(conn.cursor()) as cr:
        cr.execute("UPDATE users SET webhook_url = ? WHERE id = ?", [webhook_url, user_id])
        conn.commit()
        return cr.fetchone()
