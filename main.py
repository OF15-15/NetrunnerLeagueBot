import asyncio
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

with open("id.txt") as f:
    user_id = int(f.read())

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


@tasks.loop(minutes=5)
async def messenger():
    cursor.execute('''SELECT league_id, guild_id, channel_id, name, current_round, pair_times, round_interval, first_reminder, second_reminder, third_reminder
    FROM leagues WHERE leagues.pair_times is not null''')
    leagues = cursor.fetchall()
    for league in leagues:
        ia = ia_standin.Interaction(league[1], league[2], user_id, client)
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
        if not game_time_watcher.is_running(): game_time_watcher.start()
        if not clear_completed_games.is_running(): clear_completed_games.start()
        print("tournament watcher active")
    else:
        print("tournament watcher not active")

@tasks.loop(seconds=10)
async def tournament_watcher():
    cursor.execute('''SELECT tournament_id, channel_id, guild_id, round FROM cobra_tournaments WHERE active_until>?''', (time.time(),))
    for tournament in cursor.fetchall():
        tournament_id, channel_id, guild_id, round = tournament
        url = f"https://tournaments.nullsignal.games/tournaments/{tournament_id}.json"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json()
        if data["preliminaryRounds"] > round:
            ia = ia_standin.Interaction(guild_id, channel_id, user_id, client)
            cursor.execute('''UPDATE cobra_tournaments SET round=? WHERE tournament_id=? AND channel_id=?''', (data["preliminaryRounds"], tournament_id, channel_id))
            db.commit()
            await ia.response.send_message(f"Round {data['preliminaryRounds']} is paired here:\nhttps://tournaments.nullsignal.games/tournaments/{tournament_id}/rounds")
            await commands.tournament_pairings(ia)
            delay = 150
            if channel_id == 1549829759133946057 and data["preliminaryRounds"] in {1, 2, 4, 7}: delay = 300
            end_time = int(time.time() + 2400 + delay)
            await ia.response.send_message(f"Round gently (exactly) starts at <t:{int(time.time())+delay}:t> <t:{int(time.time())+delay}:R>")
            await ia.response.send_message(f"# Round gently (exactly) ends at <t:{end_time}:t> <t:{end_time}:R>")


            cursor.execute('''DELETE FROM game_timers''')
            db.commit()
            for pairing in data["rounds"][-1]:
                players = []
                for key in ("player2", "player1"):
                    p = pairing.get(key)
                    if not p or p.get("id") is None:
                        pass
                    else:
                        players.append(commands.get_player(ia, data["players"], p["id"]))
                cursor.execute("INSERT INTO game_timers (player1, player2, tournament_id, round, end_time) VALUES (?, ?, ?, ?, ?)", (players[0], players[1], pairing["table"], round, end_time))
            db.commit()

@tasks.loop(seconds=2)
async def game_time_watcher():
    cursor.execute('''SELECT player1, player2, tournament_id, round, end_time FROM game_timers WHERE end_time<?''', (int(time.time()),))
    cursor.execute('''DELETE FROM game_timers WHERE end_time<?''', (int(time.time()),))
    db.commit()
    results = cursor.fetchall()
    if len(results) == 0: return None
    chunks = ["The following games have ended:\nplayer1 - player2 - end-time\n"]
    ia = ia_standin.Interaction(372121348300079106, 1549829759133946057, user_id, client)
    for game in results:
        player1, player2, table, round, end_time = game
        msg = f"{player1} - {player2} - {end_time}\n"
        if len(chunks[-1]) + len(msg) < 2000:
            chunks[-1] += msg
        else:
            chunks.append(msg)
    for chunk in chunks:
        await ia.followup.send(chunk)

@tasks.loop(seconds=60)
async def clear_completed_games():
    url = f"https://tournaments.nullsignal.games/tournaments/{4990}.json"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()
    db.commit()
    for pairing in data["rounds"][-1]:
        if pairing["player1"]["combinedScore"] is not None:
            cursor.execute("DELETE FROM game_timers WHERE tournament_id=?", (pairing["table"],))
    db.commit()

client.run(token)