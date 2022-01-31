# -*- coding:utf-8 -*-

from edu_logger import root
import mysql.connector
import edu_connection_config as edu_connection_config

def edu_mysql_connexion():
    """
    Method to connect on mysql server
    :return: mysql connection
    """
    try:
        root.info("Start of connection to the mysql server...")
        connection = mysql.connector.connect(
            host=edu_connection_config.MYSQL_SERVER_HOST,
            port=edu_connection_config.MYSQL_SERVER_PORT,
            user=edu_connection_config.MYSQL_SERVER_USER,
            password=edu_connection_config.MYSQL_SERVER_PASSWORD,
            database=edu_connection_config.MYSQL_SERVER_DBNAME,
            charset='utf8',
        )
        if connection.is_connected():
            root.info("Connection to the mysql server success!")
            return connection
        else:
            root.info("Connection to the mysql server failed!")
            return False
    except Exception as e:
        root.info("Connection to the mysql server failed!: "+ str(e))
        return False


def edu_mysql_execute_request(connection, requests):
    """
    Method to execute sql request on mysql
    :param connection: mysql connection
    :param requests: sql request
    :return: result of request
    """
    try:
        if connection:
            root.info("Start of request to mysql server")
            cursor = connection.cursor()
            cursor.execute(requests)
            results = cursor.fetchall()
            root.info("Request on mysql server successful!")
            return results
        else:
            root.info("Request on mysql server failed!")
            return False
    except Exception as e:
        root.info("Request on mysql server failed! : "+str(e))
        return False

def edu_mysql_execute_request_count(connection, requests):
    """
    Method to execute sql request on mysql
    :param connection: mysql connection
    :param requests: sql request to count rows
    :return: result count of rows
    """
    try:
        if connection:
            root.info("Start of request count to mysql server")
            cursor = connection.cursor()
            cursor.execute(requests)
            results = cursor.fetchall()
            root.info("Request count on mysql server successful!")
            return results
        else:
            root.info("Request count on mysql server failed!")
            return False
    except Exception:
        root.info("Request on mysql server failed!")
        return False

def edu_mysql_execute_to_cursor(connection, requests):
    """
    Method to execute sql request on mysql
    :param connection: mysql connection
    :param requests: sql request
    :return: result cursor
    """
    try:
        if connection:
            cursor = connection.cursor()
            cursor.execute(requests)
            return cursor
        else:
            root.info("Request2cursor on mysql server failed!")
            return False
    except Exception:
        root.info("Request on mysql server failed!")
        return False

def edu_mysql_cursor_to_data(cursor, line_format):
    """
    Method to execute sql request on mysql
    :param cursor: cursor
    :param line_format: dict value
    :return: result data
    """
    try:
        row = cursor.fetchone()
        line_value = list(row)
        to_create = eval(line_format['value'])
        to_create.update(line_format['default'])
        return to_create
    except Exception:
        root.info("Request on mysql server failed!")
        return False