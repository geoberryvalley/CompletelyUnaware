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

@stocks.command(name="runalgorithm", description="Run the open today algorithm and send the results to Discord.")
async def runalgoritm(ctx):
    await ctx.defer()  # Acknowledge the command to avoid timeout
    result = stocks_functions.openTodayAlgo()
    await ctx.respond(result)

@stocks.command(name="closepositions", description="Close all open positions and send the results to Discord.")
async def closepositions(ctx):
    await ctx.defer()  # Acknowledge the command to avoid timeout
    result = stocks_functions.closeAllPositions()
    await ctx.respond(result)

@stocks.command(name="getcurrentpositions", description="Get all current positions and send the results to Discord.")
async def getcurrentpositions(ctx):
    await ctx.defer()  # Acknowledge the command to avoid timeout
    result = stocks_functions.checkPositions()
    await ctx.respond(result)
    

try:
    bot.run(discord_token)
finally:
    db_functions.close_pool()