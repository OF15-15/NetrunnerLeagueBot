import discord
import commands
import sqlite3
import json as js

# private bot-specific token
with open("token.txt") as f:
    token = f.read()

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

cursor.execute('''SELECT * FROM guilds''')
guilds = cursor.fetchall()
db.commit()

guild_ids = [g[0] for g in guilds]

for cmd in commands.command_list:
    tree.add_command(cmd, guilds=[discord.Object(id=g) for g in guild_ids])


@client.event
async def on_ready():
    for guild_id in guild_ids:
        await tree.sync(guild=discord.Object(id=guild_id))
    print("Ready!")
    print(f"Logged in on {', '.join([g[1] for g in guilds])}")

client.run(token)