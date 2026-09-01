import constants
import requests

def getStockData(symbolString):
    url = f"https://data.alpaca.markets/v2/stocks/bars/latest?symbols={symbolString}"
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": constants.alpaca_api_key,
        "APCA-API-SECRET-KEY": constants.alpaca_secret_key
    }
    response = None
    try:
        response = requests.get(url, headers=headers).json()["bars"]
    except Exception as e:
        print(f"Error fetching stock data for symbols {symbolString}: {e}")
        raise Exception(f"Error fetching stock data for symbols {symbolString}: {e}")
    return response