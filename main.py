from numpy import record
import requests
import json
import datetime

from filter_functions import *
from constants import *

from openai import OpenAI

import psycopg
from psycopg.rows import dict_row

OpenAIclient = OpenAI(api_key=ai_key)


r = requests.get(f'https://financialmodelingprep.com/stable/biggest-gainers?apikey={fmp_key}')

data = r.json()
filtered_data = []
for item in data:
    if all(check(item) for check in allChecks):
        filtered_data.append(item)

print("Filtered Data:")
print(filtered_data)

company_names = [item['name'] for item in filtered_data]

response = OpenAIclient.responses.create(
    model="gpt-5.6-luna",
    input=(
        "You are given a list of company names. Remove the names of companies involved in the following industries:"
        """
        SPACs
        medical research
        pharmaceuticals
        AI
        chipmaking
        crypto
        """
        "\nAdditionally, remove the names of any companies that have a recent news article mentioning:"
        """
        mergers
        going private
        """
        f"\n\nCompany names: {json.dumps(company_names)}"
    ),
    tools=[{"type": "web_search"}],
    text={
        "format": {
            "type": "json_schema",
            "name": "filtered_companies",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "filtered_company_names": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["filtered_company_names"],
                "additionalProperties": False
            }
        }
    }
)

structured_result = json.loads(response.output_text)
result_names = structured_result["filtered_company_names"]

print("AI filtered company names:")
print(result_names)

result_symbols = [item['symbol'] for item in filtered_data if item['name'] in result_names]
symbol_price_dict = {item['symbol']: item['price'] for item in filtered_data if item['name'] in result_names}
print("Resulting symbols and their prices:")
for symbol, price in symbol_price_dict.items():
    print(f"  {symbol}: {price}")

with psycopg.connect(dbstring) as conn:
    with conn.cursor(row_factory=dict_row) as cur:
        #first, close all existing positions
        cur.execute("SELECT * FROM currentpositions")

        oldPositions = cur.fetchall()
        #check if no old positions:
        if (not oldPositions):
            print("No old positions to close.")
        else: #we have old positions to close
            print("Old positions:")
            for position in oldPositions:
                print(f"  {position['symbol']}: {position['size']} shares at ${position['openprice']}")
            # Fetch the latest bar data for each symbol
            url = f"https://data.alpaca.markets/v2/stocks/bars/latest?symbols={','.join([record['symbol'] for record in oldPositions])}"
            headers = {
                "accept": "application/json",
                "APCA-API-KEY-ID": alpaca_api_key,
                "APCA-API-SECRET-KEY": alpaca_secret_key
            }
            response = requests.get(url, headers=headers).json()["bars"]

            for record in oldPositions:
                size = record['size'] #long = positive, short = negative
                openprice = record['openprice']
                closeprice = response[record['symbol']]['c']
                cur.execute("INSERT INTO historicalpositions (index, symbol, size, openprice, opentime, closeprice, closetime) VALUES (%s, %s, %s, %s, %s, %s, %s)", (record['index'], record['symbol'], size, openprice, record['opentime'], closeprice, datetime.datetime.now()))
                cur.execute("DELETE FROM currentpositions WHERE index = %s", (record['index'],))
                cur.execute("UPDATE currentbalance SET balance = balance + %s WHERE index = 0", (size * closeprice, ))

        #second, update historical balance
        cur.execute("SELECT balance FROM currentbalance WHERE index = 0")
        newBalance = cur.fetchone()
        if newBalance == None:
            raise Exception("No balance found in currentbalance table.")
        newBalance = newBalance['balance']
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        cur.execute("INSERT INTO historicalbalance (balance, index, date) VALUES (%s, %s, %s)", (newBalance, 0, yesterday))

        #third, open new positions
        for symbol in result_symbols:
            price = symbol_price_dict[symbol]
            size = int(newBalance / len(result_symbols) / price) * -1  # Short position, hence negative size
            if size == 0:
                print(f"Not enough balance to short any shares of {symbol}. Skipping.")
                continue
            cur.execute("INSERT INTO currentpositions (symbol, size, openprice, opentime) VALUES (%s, %s, %s, %s)", (symbol, size, price, datetime.datetime.now()))
            cur.execute("UPDATE currentbalance SET balance = balance - %s WHERE index = 0", (size * price, ))
            print(f"Opened short position for {symbol}: {size} shares at ${price}")