from contextlib import contextmanager

import mysql.connector
from flask import current_app


def get_connection():
    return mysql.connector.connect(
        host=current_app.config["MYSQL_HOST"],
        port=current_app.config["MYSQL_PORT"],
        user=current_app.config["MYSQL_USER"],
        password=current_app.config["MYSQL_PASSWORD"],
        database=current_app.config["MYSQL_DATABASE"],
    )


@contextmanager
def db_cursor(dictionary=True):
    connection = get_connection()
    cursor = connection.cursor(dictionary=dictionary)
    try:
        yield connection, cursor
        connection.commit()
    finally:
        cursor.close()
        connection.close()
