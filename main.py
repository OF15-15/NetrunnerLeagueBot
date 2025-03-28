import time
import ia_standin
import discord
import commands
import sqlite3
import json as js
from discord.ext import tasks
import aiohttp

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
    messenger.start()


@tasks.loop(minutes=1)
async def messenger():
    cursor.execute('''SELECT league_id, guild_id, channel_id, name, current_round, pair_times, round_interval, first_reminder, second_reminder, third_reminder
    FROM leagues WHERE leagues.pair_times is not null''')
    leagues = cursor.fetchall()
    for league in leagues:
        ia = ia_standin.Interaction(league[1], league[2], 1232430844891758623, client)
        if league[5] < time.time():
            new_round = league[5] + league[6]*60*60*24
            msg = f"This round will close roughly on <t:{new_round}:F> which is <t:{new_round}:R>."
            cursor.execute('''UPDATE leagues SET pair_times=?, first_reminder=?, second_reminder=?, third_reminder=? WHERE league_id=?''',
                           (new_round, abs(league[7]), abs(league[8]), abs(league[9]), league[0]))
            await commands.pair(ia, msg)
        elif league[5] - league[7] * 3600 < time.time():
            msg = f"This round will close roughly on <t:{league[5]}:F> which is <t:{league[5]}:R>. Please remember to get your games in :)"
            cursor.execute('''UPDATE leagues SET first_reminder=? WHERE league_id=?''', (-league[7], league[0]))
            await commands.reminder(ia, msg)
        elif league[5] - league[8] * 3600 < time.time():
            msg = f"This round will close roughly on <t:{league[5]}:F> which is <t:{league[5]}:R>. Please remember to get your games in :) :)"
            cursor.execute('''UPDATE leagues SET second_reminder=? WHERE league_id=?''', (-league[8], league[0]))
            await commands.reminder(ia, msg)
        elif league[5] - league[9] * 3600 < time.time():
            msg = f"This round will close roughly on <t:{league[5]}:F> which is <t:{league[5]}:R>. Please remember to get your games in :) :) :)"
            cursor.execute('''UPDATE leagues SET third_reminder=? WHERE league_id=?''', (-league[9], league[0]))
            await commands.reminder(ia, msg)
        db.commit()

    # cobra tournaments
    cursor.execute('''SELECT tournament_id FROM cobra_tournaments WHERE active_until>?''', (time.time(),))
    if len(cursor.fetchall()) > 0:
        if not tournament_watcher.is_running(): tournament_watcher.start()
        print("tournament watcher active")
    else:
        tournament_watcher.stop()
        print("tournament watcher not active")

@tasks.loop(seconds=10)
async def tournament_watcher():
    cursor.execute('''SELECT tournament_id, channel_id, round FROM cobra_tournaments WHERE active_until>?''', (time.time(),))
    for tournament in cursor.fetchall():
        tournament_id, channel_id, round = tournament
        url = f"https://tournaments.nullsignal.games/tournaments/{tournament_id}.json"
        async with aiohttp.ClientSession() as session:
            raw_data = await session.get(url)
        data = await raw_data.json()
        if data["preliminaryRounds"] > round:
            print("foo 1234")
            cursor.execute('''UPDATE cobra_tournaments SET round=? WHERE tournament_id=?''', (data["preliminaryRounds"], tournament_id))
            db.commit()


client.run(token)