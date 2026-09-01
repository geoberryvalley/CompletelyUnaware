from numpy import record
import requests
import json
import datetime
import alpaca

from filter_functions import *
from constants import *

from openai import OpenAI

import db_functions

OpenAIclient = OpenAI(api_key=ai_key)

def openAccount(discID):
    if db_functions.has_account(discID):
        return "Error: An account already exists for this Discord ID."
    db_functions.open_account(discID)
    return "Account successfully opened with a starting balance of $10,000."

def openTodayAlgo(discID):
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

    symbol_price_dict = {item['symbol']: item['price'] for item in filtered_data if item['name'] in result_names}
    curBalance = db_functions.get_current_balance(discID)
    assert curBalance is not None, "Current balance is None. Please check the database."
    curBalance = round(curBalance['balance'], 2)

    retInfo = "## OPENING NEW POSITIONS:\n"
    print("Opened positions:")
    for symbol, price in symbol_price_dict.items():
        size = int(curBalance / price / len(symbol_price_dict))
        db_functions.open_position(symbol, size, price, discID)
        print(f"  {symbol}: {size} shares at ${price}")
        retInfo += f"- Opened position for {symbol}: {size} shares at ${price}\n"

    return retInfo

def closeAllPositions(discID):
    if not db_functions.has_account(discID):
        return "Error: No account found for this Discord ID. Please open an account first."
    retInfo = "## CLOSING ALL POSITIONS:\n"
    oldPositions = db_functions.get_current_positions(discID)
    if not oldPositions:
        print("No current positions to close.")
        retInfo += "No current positions to close.\n"
    else:
        print("Old positions:")
        for position in oldPositions:
            print(f"  {position['symbol']}: {position['size']} shares at ${position['openprice']}")
        # Fetch the latest bar data for each symbol
        symbolString = ','.join([record['symbol'] for record in oldPositions])
        response = None
        try:
            response = alpaca.getStockData(symbolString)  # Check if the symbol is valid
        except Exception as e:
            print(f"Error: {e}")
            return f"Error: Unable to retrieve data for symbol {symbolString}. Please check the symbol and try again."

        for position in oldPositions:
            symbol = position['symbol']
            size = position['size']
            openprice = position['openprice']
            closeprice = response[symbol]['c']  # Get the closing price from the latest bar data
            db_functions.close_position(symbol, closeprice, discID)
            print(f"Closed position for {symbol}: {size} shares at ${openprice} (now ${closeprice})")
            retInfo += f"- Closed position for {symbol}: {size} shares at ${openprice} (now ${closeprice})\n"

        db_functions.record_balance(discID)
        retInfo += "\n## UPDATED HISTORICAL BALANCE:\n"
        newBalance = db_functions.get_current_balance(discID)
        assert newBalance is not None, "Current balance is None. Please check the database."
        newBalance = round(newBalance['balance'], 2)
        retInfo += f"New balance: ${newBalance}\n"
    return retInfo

def checkPositions(discID):
    if not db_functions.has_account(discID):
        return "Error: No account found for this Discord ID. Please open an account first."
    retInfo = "## CURRENT POSITIONS:\n"
    openPositions = db_functions.get_current_positions(discID)
    if not openPositions:
        print("No current positions.")
        retInfo += "No current positions.\n"
    else:
        print("Open positions:")
        # Fetch the latest bar data for each symbol
        symbolString = ','.join([record['symbol'] for record in openPositions])
        response = None
        try:
            response = alpaca.getStockData(symbolString)  # Check if the symbol is valid
        except Exception as e:
            print(f"Error: {e}")
            return f"Error: Unable to retrieve data for symbols {symbolString}."
        for position in openPositions:
            symbol = position['symbol']
            curprice = response[symbol]['c']  # Get the current price from the latest bar data
            delta_percent = round(((curprice - position['openprice']) / position['openprice']) * 100, 2)
            print(f"  {position['symbol']}: {position['size']} shares at ${position['openprice']} | (current price: ${curprice}, change: {delta_percent}%)")
            retInfo += f"- {position['symbol']}: {position['size']} shares at ${position['openprice']} | (current price: ${curprice}, change: {delta_percent}%)"

    curBalance = db_functions.get_current_balance(discID)
    assert curBalance is not None, "Current balance is None. Please check the database."
    curBalance = round(curBalance['balance'], 2)
    retInfo += f"\n\n## CURRENT BALANCE:\n- ${curBalance}\n"
    return retInfo

def lookupSymbol(symbol):
    response = None
    try:
        response = alpaca.getStockData(symbol)  # Check if the symbol is valid
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: Unable to retrieve data for symbol {symbol}. Please check the symbol and try again."
    retInfo = f"""## SYMBOL LOOKUP: {symbol}
    Current price: ${response[symbol]['c']}
    Open price: ${response[symbol]['o']}
    High price: ${response[symbol]['h']}
    Low price: ${response[symbol]['l']}
    Percent change since open: {round(((response[symbol]['c'] - response[symbol]['o']) / response[symbol]['o']) * 100, 2)}%
    """
    return retInfo

def openPosition(symbol, size, discID):
    if not db_functions.has_account(discID):
        return "Error: No account found for this Discord ID. Please open an account first."
    response = None
    try:
        response = alpaca.getStockData(symbol)  # Check if the symbol is valid
        assert ',' not in symbol, "Invalid symbol format. Please provide a single stock symbol."
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: Unable to retrieve data for symbol {symbol}. Please check the symbol and try again."
    price = response[symbol]['c']  # Get the current price from the latest bar data
    db_functions.open_position(symbol, size, price, discID)
    retInfo = f"Opened position for {symbol}: {size} shares at ${price}"
    try:
        curBalance = db_functions.get_current_balance(discID)
        assert curBalance is not None, "Current balance is None. Please check the database."
        curBalance = round(curBalance['balance'], 2)
        retInfo += f"\n\n## CURRENT BALANCE:\n- ${curBalance}\n"
    except AssertionError as e:
        print(f"Error: {e}")
        retInfo += "\n\n## CURRENT BALANCE:\n- Error retrieving current balance. Please check the database.\n"
    return retInfo

def closePosition(symbol, discID):
    if not db_functions.has_account(discID):
        return "Error: No account found for this Discord ID. Please open an account first."
    response = None
    try:
        assert ',' not in symbol, "Invalid symbol format. Please provide a single stock symbol."
        response = alpaca.getStockData(symbol)  # Check if the symbol is valid
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: Unable to retrieve data for symbol {symbol}. Please check the symbol and try again."
    closeprice = response[symbol]['c']  # Get the current price from the latest bar data
    try:
        db_functions.close_position(symbol, closeprice, discID)
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: Unable to close position for symbol {symbol}. Please check if the position exists and try again."
    return f"Closed position for {symbol} at ${closeprice}."

def getHistoricalBalance(discID):
    if not db_functions.has_account(discID):
        return "Error: No account found for this Discord ID. Please open an account first."
    historical_balance = db_functions.get_historical_balance(discID)
    if not historical_balance:
        return "No historical balance records found."
    retInfo = "## HISTORICAL BALANCE:\n"
    for record in historical_balance:
        retInfo += f"- ${record['balance']} at {record['datetime']}\n"
    return retInfo

def getHistoricalPositions(discID):
    if not db_functions.has_account(discID):
        return "Error: No account found for this Discord ID. Please open an account first."
    historical_positions = db_functions.get_historical_positions(discID)
    if not historical_positions:
        return "No historical position records found."
    retInfo = "## HISTORICAL POSITIONS:\n"
    for record in historical_positions:
        retInfo += f"- {record['symbol']}: {record['size']} shares at ${record['price']} on {record['datetime']}\n"
    return retInfo