import discord
import commands
import sqlite3
import json as js

# private bot-specific token
with open("token.txt") as f:
    token = f.read()

# all the data
with open("data.json") as f:
    guilds_data = js.load(f)

# create client object and a command tree for /-commands
intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

# connect to the database
db = sqlite3.connect("db.sqlite")
cursor = db.cursor()
# make db accessible from commands.py
commands.db = db
commands.cursor = cursor


for cmd in commands.command_list:
    tree.add_command(cmd, guilds=[discord.Object(id=g["guild_id"]) for g in guilds_data])


@client.event
async def on_ready():
    for guild in guilds_data:
        await tree.sync(guild=discord.Object(id=guild["guild_id"]))
    print("Ready!")

client.run(token)