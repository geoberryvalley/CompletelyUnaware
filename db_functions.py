import psycopg
import datetime
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

import constants

pool = ConnectionPool(constants.dbstring, min_size=1, max_size=10)

def close_pool():
    pool.close()

def get_current_positions():
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM currentpositions")
            return cur.fetchall()

def get_current_balance():
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM currentbalance")
            return cur.fetchone()

def open_position(symbol, size, price):
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            #first, check to see if the position exists already
            cur.execute("SELECT * FROM currentpositions WHERE symbol = %s", (symbol,))
            existing_position = cur.fetchone()
            if existing_position is not None:
                if existing_position['size'] + size != 0:
                    cur.execute("UPDATE currentpositions SET size = size + %s, openprice = %s, opentime = %s WHERE symbol = %s", (size, price, datetime.datetime.now(), symbol))
                else:
                    cur.execute("DELETE FROM currentpositions WHERE symbol = %s", (symbol,))
                    record_balance()  # Record the balance after closing the position
            else:
                cur.execute("INSERT INTO currentpositions (symbol, size, openprice, opentime) VALUES (%s, %s, %s, %s)", (symbol, size, price, datetime.datetime.now()))
            cur.execute("UPDATE currentbalance SET balance = balance - %s WHERE index = 0", (size * price, ))

def close_position(symbol, closeprice):
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM currentpositions WHERE symbol = %s", (symbol,))
            position = cur.fetchone()
            if position is None:
                raise Exception(f"No current position found for symbol {symbol}.")
            size = position['size']
            openprice = position['openprice']
            cur.execute("INSERT INTO historicalpositions (index, symbol, size, openprice, opentime, closeprice, closetime) VALUES (%s, %s, %s, %s, %s, %s, %s)", (position['index'], symbol, size, openprice, position['opentime'], closeprice, datetime.datetime.now()))
            cur.execute("DELETE FROM currentpositions WHERE index = %s", (position['index'],))
            cur.execute("UPDATE currentbalance SET balance = balance + %s WHERE index = 0", (round(size * closeprice, 2), ))
            record_balance()  # Record the balance after closing the position


def record_balance():
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT balance FROM currentbalance WHERE index = 0")
            current_balance = cur.fetchone()
            if current_balance is None:
                raise Exception("No current balance found. Please check the database.")
            current_balance = round(current_balance['balance'], 2)
            cur.execute("INSERT INTO historicalbalance (balance, index, datetime) VALUES (%s, %s, %s)", (current_balance, 0, datetime.datetime.now()))