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

@stocks.command(name="openaccount", description="Open a new account with $10,000 starting balance.")
async def openaccount(ctx):
    await ctx.defer()
    result = stocks_functions.openAccount(ctx.author.id)
    await ctx.respond(result)

#removed command because im opening up the bot and i dont want to waste my credits

# @stocks.command(name="runalgorithm", description="Run the open today algorithm.")
# async def runalgoritm(ctx):
#     await ctx.defer()  # Acknowledge the command to avoid timeout
#     result = stocks_functions.openTodayAlgo()
#     await ctx.respond(result)

@stocks.command(name="closeall", description="Close all open positions.")
async def closeall(ctx):
    await ctx.defer()  # Acknowledge the command to avoid timeout
    result = stocks_functions.closeAllPositions(ctx.author.id)
    await ctx.respond(result)

@stocks.command(name="checkaccount", description="Get all current positions and account balance.")
async def getcurrentpositions(ctx):
    await ctx.defer()  # Acknowledge the command to avoid timeout
    result = stocks_functions.checkPositions(ctx.author.id)
    await ctx.respond(result)

@stocks.command(name="lookupsymbol", description="Lookup a stock symbol.")
async def lookupsymbol(ctx, symbol: str):
    await ctx.defer()  # Acknowledge the command to avoid timeout
    result = stocks_functions.lookupSymbol(symbol)
    await ctx.respond(result)

@stocks.command(name="position", description="Open a position for a stock symbol. Enter a negative number to short.")
async def position(ctx, symbol: str, size: int):
    await ctx.defer()  # Acknowledge the command to avoid timeout
    result = stocks_functions.openPosition(symbol, size, ctx.author.id)
    await ctx.respond(result)

@stocks.command(name="close", description="Close a position for a stock symbol.")
async def close(ctx, symbol: str):
    await ctx.defer()  # Acknowledge the command to avoid timeout
    result = stocks_functions.closePosition(symbol, ctx.author.id)
    await ctx.respond(result)

@stocks.command(name="balancehistory", description="Get the balance history of your account.")
async def balancehistory(ctx):
    await ctx.defer()  # Acknowledge the command to avoid timeout
    result = stocks_functions.getHistoricalBalance(ctx.author.id)
    await ctx.respond(result)

@stocks.command(name="positionhistory", description="Get the position history of your account.")
async def positionhistory(ctx):
    await ctx.defer()  # Acknowledge the command to avoid timeout
    result = stocks_functions.getHistoricalPositions(ctx.author.id)
    await ctx.respond(result)

try:
    bot.run(discord_token)
finally:
    db_functions.close_pool()