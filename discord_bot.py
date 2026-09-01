#send the message to discord
import discord
from constants import *
import stocks_functions
import db_functions

bot = discord.Bot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

stocks = bot.create_group("stocks", "Commands related to stock trading")

@stocks.command(name="runalgorithm", description="Run the open today algorithm.")
async def runalgoritm(ctx):
    await ctx.defer()  # Acknowledge the command to avoid timeout
    result = stocks_functions.openTodayAlgo()
    await ctx.respond(result)

@stocks.command(name="closepositions", description="Close all open positions.")
async def closepositions(ctx):
    await ctx.defer()  # Acknowledge the command to avoid timeout
    result = stocks_functions.closeAllPositions()
    await ctx.respond(result)

@stocks.command(name="checkaccount", description="Get all current positions and account balance.")
async def getcurrentpositions(ctx):
    await ctx.defer()  # Acknowledge the command to avoid timeout
    result = stocks_functions.checkPositions()
    await ctx.respond(result)

@stocks.command(name="lookupsymbol", description="Lookup a stock symbol.")
async def lookupsymbol(ctx, symbol: str):
    await ctx.defer()  # Acknowledge the command to avoid timeout
    result = stocks_functions.lookupSymbol(symbol)
    await ctx.respond(result)

@stocks.command(name="buy", description="Buy a stock symbol.")
async def buy(ctx, symbol: str, size: int):
    await ctx.defer()  # Acknowledge the command to avoid timeout
    result = stocks_functions.openPosition(symbol, size)
    await ctx.respond(result)

try:
    bot.run(discord_token)
finally:
    db_functions.close_pool()