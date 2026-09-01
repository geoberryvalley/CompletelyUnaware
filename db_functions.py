import psycopg
import datetime
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

import constants

pool = ConnectionPool(constants.dbstring, min_size=1, max_size=10)

def close_pool():
    pool.close()

def open_account(discID):
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("INSERT INTO currentbalance (userid, balance) VALUES (%s, %s)", (discID, 10000.0))
            cur.execute("INSERT INTO historicalbalance (userid, balance, datetime) VALUES (%s, %s, %s)", (discID, 10000.0, datetime.datetime.now()))

def get_current_positions(discID):
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM currentpositions WHERE userid = %s", (discID,))
            return cur.fetchall()

def get_current_balance(discID):
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM currentbalance WHERE userid = %s", (discID,))
            return cur.fetchone()

def open_position(symbol, size, price, discID):
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            #first, check to see if the position exists already
            cur.execute("SELECT * FROM currentpositions WHERE symbol = %s AND userid = %s", (symbol, discID))
            existing_position = cur.fetchone()
            if existing_position is not None:
                if existing_position['size'] + size != 0:
                    cur.execute("UPDATE currentpositions SET size = size + %s, openprice = %s, opentime = %s WHERE symbol = %s AND userid = %s", (size, price, datetime.datetime.now(), symbol, discID))
                else:
                    cur.execute("DELETE FROM currentpositions WHERE symbol = %s AND userid = %s", (symbol, discID))
                    record_balance(discID)  # Record the balance after closing the position
            else:
                cur.execute("INSERT INTO currentpositions (userid, symbol, size, openprice, opentime) VALUES (%s, %s, %s, %s)", (discID, symbol, size, price, datetime.datetime.now()))
            cur.execute("UPDATE currentbalance SET balance = balance - %s WHERE userid = %s", (size * price, discID))

def close_position(symbol, closeprice, discID):
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM currentpositions WHERE symbol = %s AND userid = %s", (symbol, discID))
            position = cur.fetchone()
            if position is None:
                raise Exception(f"No current position found for symbol {symbol}.")
            size = position['size']
            openprice = position['openprice']
            cur.execute("DELETE FROM currentpositions WHERE symbol = %s AND userid = %s", (symbol, discID))
            cur.execute("UPDATE currentbalance SET balance = balance + %s WHERE userid = %s", (round(size * closeprice, 2), discID))
            record_balance(discID)  # Record the balance after closing the position

def get_historical_balance(discID):
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM historicalbalance WHERE userid = %s ORDER BY datetime DESC LIMIT 100", (discID,))
            return cur.fetchall()

def get_historical_positions(discID):
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM historicalpositions WHERE userid = %s ORDER BY closetime DESC LIMIT 100", (discID,))
            return cur.fetchall()


def record_balance(discID):
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT balance FROM currentbalance WHERE userid = %s", (discID,))
            current_balance = cur.fetchone()
            if current_balance is None:
                raise Exception("No current balance found. Please check the database.")
            current_balance = round(current_balance['balance'], 2)
            cur.execute("INSERT INTO historicalbalance (balance, userid, datetime) VALUES (%s, %s, %s)", (current_balance, discID, datetime.datetime.now()))

def has_account(discID):
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM currentbalance WHERE userid = %s", (discID,))
            return cur.fetchone() is not None