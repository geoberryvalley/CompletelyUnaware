def priceCheck(item):
    return item['price'] >= 2 and item['price'] <= 10

def ETFCheck(item):
    return not 'ETF' in item['name']

def changeCheck(item):
    return item['changesPercentage'] >= 30

allChecks = [priceCheck, ETFCheck, changeCheck]