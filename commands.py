import asyncio
import inspect
import time
import discord
import sqlite3
import functools
import json as js
import random as rd
import mwmatching as mwm
from discord.ext import tasks
import aiohttp

def command(name, description, perms):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(ia, *args, **kwargs):
            if perms == "everyone":
                pass
            elif auth_admin(ia.guild_id, ia.user.id):
                pass
            else:
                return await ia.response.send_message(f"Du darfst diesen Befehl nicht benutzen", ephemeral=True)
            await func(ia, *args, **kwargs)

        command_list.append(discord.app_commands.Command(callback=wrapper, name=name, description=description))
        return wrapper
    return decorator

command_list = []

db: sqlite3.Connection
cursor: sqlite3.Cursor


def auth_admin(guild, user):
    if int(user) == 1232430844891758623:
        return True
    cursor.execute('''SELECT * FROM admins WHERE guild_id = ? AND user_id=?''', (guild, user))
    owner = cursor.fetchone()
    db.commit()
    if owner is None:
        return False
    return True

"""
@command("echo", "Echo the string put in", "admin")
async def echo(ia, content: str):
    await ia.response.send_message(content)"""

@command("create", "Create a new league", "admin")
async def create_league(ia, name: str):
    cursor.execute('''INSERT INTO leagues VALUES (?, ?, ?, ?, ?, null, null, null, null, null)''', (None, ia.guild_id, ia.channel_id, name, 0))
    db.commit()
    await ia.response.send_message(f"You created league {name} in this channel")

@command("delete_league", "Delete the league in this channel", "admin")
async def delete_league(ia):
    cursor.execute('''DELETE FROM leagues WHERE channel_id=?''', (ia.channel_id, ))
    db.commit()
    await ia.response.send_message(f"You deleted the league in this channel")

@command("pause_league", "Pause the league in this channel", "admin")
async def pause_league(ia):
    cursor.execute(
        '''UPDATE leagues SET pair_times=? WHERE channel_id=? ''',
        (None, ia.channel_id))
    db.commit()
    await ia.response.send_message(f"You paused the league in this channel")

@command("add_admin", "Add an admin", "admin")
async def add_admin(ia, admin_id: str, guild_id: str):
    if ia.user.id != 849206816172802068:
        return await ia.response.send_message("no access", ephemeral=True)
    cursor.execute('''INSERT INTO admins VALUES (?, ?)''', (int(admin_id), int(guild_id)))
    db.commit()
    await ia.response.send_message(f"Admin <@{admin_id}> added to guild {guild_id}", ephemeral=True)
@command("add_guild", "Add a guild", "admin")
async def add_guild(ia, guild_id: str, name: str):
    if ia.user.id != 849206816172802068:
        return await ia.response.send_message("no access", ephemeral=True)
    cursor.execute('''INSERT INTO guilds VALUES (?, ?)''', (int(guild_id), name))
    db.commit()
    await ia.response.send_message(f"added guild {guild_id}", ephemeral=True)

@command("join", "Join the league in this channel", "everyone")
async def join(ia):
    cursor.execute('''SELECT league_id, name FROM leagues WHERE channel_id=?''', (ia.channel.id,))
    league = cursor.fetchone()
    db.commit()
    if league is None:
        return await ia.response.send_message("No league in this channel", ephemeral=True)
    await ia.response.send_message(f"You joined {league[1]}", ephemeral=True)
    try:
        cursor.execute('''INSERT INTO player_leagues VALUES (?, ?)''', (ia.user.id, league[0]))
        db.commit()
    except:
        print("double join ?!")

@command("remove_player", "Remove a player", "admin")
async def remove_player(ia, player: str):
    player_id = player[2:-1]
    cursor.execute('''SELECT league_id, name FROM leagues WHERE channel_id=?''', (ia.channel.id,))
    league_id, name = cursor.fetchone()[0:2]
    cursor.execute('''DELETE FROM player_leagues WHERE user_id=? AND league_id=?''', (player_id, league_id))
    db.commit()
    await ia.response.send_message(f"You removed <@{player_id}> from this league", ephemeral=True)

@command("leave", "Leave the league in this channel", "everyone")
async def leave(ia):
    cursor.execute('''SELECT league_id, name FROM leagues WHERE channel_id=?''', (ia.channel.id,))
    league_id, name = cursor.fetchone()[0:2]
    cursor.execute('''DELETE FROM player_leagues WHERE user_id=? AND league_id=?''', (ia.user.id, league_id))
    db.commit()
    await ia.response.send_message(f"You left league {name}", ephemeral=True)

@command("status", "check whether you are currently in this league", "everyone")
async def status(ia):
    cursor.execute('''SELECT leagues.name FROM leagues, player_leagues WHERE channel_id=? AND leagues.league_id=player_leagues.league_id AND user_id=?''', (ia.channel_id, ia.user.id))
    all = cursor.fetchall()
    if len(all) > 0:
        await ia.response.send_message(f"You are currently a member of league {all[0][0]}", ephemeral=True)
    await ia.response.send_message(f"You are no member of a league in this channel", ephemeral=True)

@command("standings", "check the current standings", "everyone")
async def standings(ia, from_previous_round: int = None, all: str = None, show_old_players: str = None):
    cursor.execute('''SELECT league_id, current_round FROM leagues WHERE channel_id=?''', (ia.channel_id,))
    try:
        league_id, current_round = cursor.fetchone()
    except TypeError:
        return await ia.response.send_message("No league in this channel", ephemeral=True)
    if from_previous_round is not None:
        current_round = from_previous_round
    cursor.execute('''SELECT pl.user_id FROM player_leagues as pl WHERE pl.league_id=?''', (league_id,))
    players = [p[0] for p in cursor.fetchall()]
    cursor.execute('''SELECT player1_id, player2_id, result, round FROM matches WHERE league_id=?''', (league_id, ))
    matches = cursor.fetchall()

    points = {player: 0 for player in players}

    for match in matches:
        if match[0] not in points:
            points[match[0]] = 0
            if show_old_players is not None and match[1]: players.append(match[0])
        if match[1] not in points:
            points[match[1]] = 0
            if show_old_players is not None and match[1]: players.append(match[1])
        # sweep1 sweep2 corp runner id 2411 2412 tie1 tie2 tietie bye
        if (match[3] > current_round - 5 or all is not None) and match[3] <= current_round:
            match match[2]:
                case 0 | 5:
                    points[match[0]] += 6
                case 1 | 6:
                    points[match[1]] += 6
                case 2 | 3 | 4:
                    points[match[0]] += 3
                    points[match[1]] += 3
                case 7:
                    points[match[0]] += 4
                    points[match[1]] += 1
                case 8:
                    points[match[0]] += 1
                    points[match[1]] += 4
                case 9:
                    points[match[0]] += 2
                    points[match[1]] += 2
                case 10:
                    points[match[0]] += 6
    msg = ''
    players.sort(key=lambda p: points[p])
    for player in players:
        player_obj = ia.guild.get_member(player)
        if player_obj is not None:
            msg += f'{player_obj.mention}: {points[player]}\n'
        else:
            msg += f'{player}: {points[player]}\n'
    if msg == '': msg = "This league is currently empty."
    await ia.response.send_message(msg, ephemeral=True)


@command("report", "Report one of your matches", "everyone")
async def report(ia, opponent: str, left_player_score: int, right_player_score: int, context: str = None):
    #results = ["swept", "got swept", "corp split", "runner splity", "id", "won 241", "lost 241", "won->tie", "lost->tie", "tie->tie", "bye"]
    opponent_id = opponent[2:-1]
    if left_player_score == right_player_score == 3:
        if context == "id":
            result = 4
        elif context in ['c', 'corp', 'corp split']:
            result = 2
        elif context in ['r', 'runner', 'runner split']:
            result = 3
        else:
            result = 4
            # return await ia.response.send_message(f"Please specify whether the result was id, corp split or runner split in the last argument", ephemeral=True)
    elif left_player_score == 6 and right_player_score == 0:
        if context == "241":
            result = 5
        else:
            result = 0
    elif left_player_score == 0 and right_player_score == 6:
        if context == "241":
            result = 6
        else:
            result = 1
    elif left_player_score == 4 and right_player_score == 1:
        result = 7
    elif left_player_score == 1 and right_player_score == 4:
        result = 8
    else:
        return await ia.response.send_message(f"I couldn't understand the result.", ephemeral=True)
    cursor.execute('''SELECT league_id, current_round FROM leagues WHERE channel_id=?''', (ia.channel_id,))
    league_id, current_round = cursor.fetchone()
    cursor.execute('''SELECT result, round FROM matches WHERE league_id=? AND (player1_id=? AND player2_id=? OR player1_id=? AND player2_id=?)''',
                   (league_id, ia.user.id, opponent_id, opponent_id, ia.user.id))
    data = cursor.fetchall()
    if len(data) == 0:
        return await ia.response.send_message(f"You never played against <@{opponent_id}> here", ephemeral=True)
    data.sort(key=lambda x: x[1], reverse=True)
    cursor.execute('''UPDATE matches SET result=? WHERE league_id=? AND (player1_id=? AND player2_id=? OR player1_id=? AND player2_id=?) AND round=?''',
                   (result, league_id, ia.user.id, opponent_id, opponent_id, ia.user.id, data[0][1]))
    db.commit()
    if data[0][0] == -1:
        return await ia.response.send_message(f"You reported {left_player_score} - {right_player_score} against <@{opponent_id}>", ephemeral=True)
    return await ia.response.send_message(f"You reported {left_player_score} - {right_player_score} against <@{opponent_id}>. This score was already reported before.", ephemeral=True)

@command("reminder", "remind unplayed games, show results to others", "admin")
async def reminder(ia, extra_message: str = ''):
    cursor.execute('''SELECT league_id, current_round FROM leagues WHERE channel_id=?''', (ia.channel_id,))
    league_id, current_round = cursor.fetchone()
    cursor.execute('''SELECT player1_id, player2_id, result FROM matches WHERE league_id=? and round=?''', (league_id, current_round))
    data = cursor.fetchall()
    msg = extra_message + '\n' if extra_message else ''
    for item in data:
        print(item)
        match item[2]:
            case -1: msg += f'{ia.guild.get_member(item[0]).mention} ? - ? {ia.guild.get_member(item[1]).mention}'
            case 0: msg += f'{ia.guild.get_member(item[0]).name} 6 - 0 {ia.guild.get_member(item[1]).name}'
            case 1: msg += f'{ia.guild.get_member(item[0]).name} 0 - 6 {ia.guild.get_member(item[1]).name}'
            case 2: msg += f'{ia.guild.get_member(item[0]).name} 3 - 3 {ia.guild.get_member(item[1]).name} (C)'
            case 3: msg += f'{ia.guild.get_member(item[0]).name} 3 - 3 {ia.guild.get_member(item[1]).name} (R)'
            case 4: msg += f'{ia.guild.get_member(item[0]).name} 3 - 3 {ia.guild.get_member(item[1]).name} (ID)'
            case 5: msg += f'{ia.guild.get_member(item[0]).name} 6 - 0 {ia.guild.get_member(item[1]).name} (241)'
            case 6: msg += f'{ia.guild.get_member(item[0]).name} 0 - 6 {ia.guild.get_member(item[1]).name} (241)'
            case 7: msg += f'{ia.guild.get_member(item[0]).name} 4 - 1 {ia.guild.get_member(item[1]).name}'
            case 8: msg += f'{ia.guild.get_member(item[0]).name} 1 - 4 {ia.guild.get_member(item[1]).name}'
            case 9: msg += f'{ia.guild.get_member(item[0]).name} 2 - 2 {ia.guild.get_member(item[1]).name}'
            case 10: msg += f'{ia.guild.get_member(item[0]).name} 6 - 0 {"BYE":>21}'
        msg += '\n'
    return await ia.response.send_message(msg, ephemeral=False)

@command("results", "View the last round's results ", "everyone")
async def results(ia, round: str = "current"):
    cursor.execute('''SELECT league_id, current_round FROM leagues WHERE channel_id=?''', (ia.channel_id,))
    league_id, cr = cursor.fetchone()
    try:
        current_round = int(round)
    except ValueError:
        current_round = int(cr)
    cursor.execute('''SELECT player1_id, player2_id, result FROM matches WHERE league_id=? and round=?''', (league_id, current_round))
    data = cursor.fetchall()
    msg = ''
    for item in data:
        match item[2]:
            case -1: msg += f'<@{item[0]}> ? - ? <@{item[1]}>'
            case 0: msg += f'<@{item[0]}> 6 - 0 <@{item[1]}>'
            case 1: msg += f'<@{item[0]}> 0 - 6 <@{item[1]}>'
            case 2: msg += f'<@{item[0]}> 3 - 3 <@{item[1]}> (C)'
            case 3: msg += f'<@{item[0]}> 3 - 3 <@{item[1]}> (R)'
            case 4: msg += f'<@{item[0]}> 3 - 3 <@{item[1]}> (ID)'
            case 5: msg += f'<@{item[0]}> 6 - 0 <@{item[1]}> (241)'
            case 6: msg += f'<@{item[0]}> 0 - 6 <@{item[1]}> (241)'
            case 7: msg += f'<@{item[0]}> 4 - 1 <@{item[1]}>'
            case 8: msg += f'<@{item[0]}> 1 - 4 <@{item[1]}>'
            case 9: msg += f'<@{item[0]}> 2 - 2 <@{item[1]}>'
            case 10: msg += f'<@{item[0]}> 6 - 0 {"BYE":>21}'
        msg += '\n'
    if msg == '':
        return await ia.response.send_message("round not found", ephemeral=True)
    return await ia.response.send_message(msg, ephemeral=True)

@command("delete_round", "Delete the last round", "admin")
async def delete_round(ia):
    cursor.execute('''SELECT league_id, current_round FROM leagues WHERE channel_id=?''', (ia.channel_id,))
    league_id, current_round = cursor.fetchone()
    cursor.execute('''DELETE FROM matches WHERE league_id=? and round=?''', (league_id, current_round))
    cursor.execute('''UPDATE leagues SET current_round=? WHERE league_id=?''', (current_round-1, league_id))
    db.commit()

@command("pair", "Pair a new round", "admin")
async def pair(ia, extra_message:str = ''):
    cursor.execute('''SELECT league_id, current_round FROM leagues WHERE channel_id=?''', (ia.channel_id,))
    league_id, current_round = cursor.fetchone()
    cursor.execute('''SELECT pl.user_id FROM player_leagues as pl WHERE pl.league_id=?''', (league_id,))
    players = [p[0] for p in cursor.fetchall()]
    cursor.execute('''SELECT player1_id, player2_id, result, round FROM matches WHERE league_id=?''', (league_id, ))
    matches = cursor.fetchall()
    pairings = dss(players, matches, current_round)
    if len(pairings) == 0:
        await ia.response.send_message("league is empty", ephemeral=True)
    msg = extra_message + ('\n' * bool(extra_message)) + f'Round {current_round}\n'
    for pairing in pairings:
        if pairing[1] == "BYE":
            msg += f"<@{pairing[0]}>" + " vs BYE\n"
        else:
            msg += f"<@{pairing[0]}> vs <@{pairing[1]}>\n"
    current_round += 1
    cursor.execute("""UPDATE leagues SET current_round=? WHERE league_id=?""", (current_round, league_id))
    cursor.executemany('''INSERT INTO matches VALUES (?, ?, ?, ?, ?, ?)''', [(None, league_id, current_round, p1, p2, -1) for p1, p2 in pairings])
    cursor.execute("""UPDATE matches SET result=? WHERE player2_id=?""", (10, 'BYE'))
    db.commit()
    await ia.response.send_message(msg)

@command("scheduled_pairing", "Pair a new round in a constant interval", "admin")
async def scheduled_pairing(ia, start_time: int, interval_days: int = 7, first_reminder_hours: int = 0, second_reminder_hours: int = 0, third_reminder_hours: int = 0):
    cursor.execute('''UPDATE leagues SET pair_times=?, round_interval=?, first_reminder=?, second_reminder=?, third_reminder=? WHERE channel_id=? ''', (start_time, interval_days, first_reminder_hours, second_reminder_hours, third_reminder_hours, ia.channel_id))
    db.commit()
    await ia.response.send_message(f"You set up a schedule for this league.\n The next round will go up on <t:{start_time}:F> with repetition every {interval_days} days.\n You set reminders {first_reminder_hours} {bool(second_reminder_hours)*(', ' + str(second_reminder_hours))}{bool(third_reminder_hours)*(' and ' + str(third_reminder_hours))} hours before each pairing.")

@command("help", "command help",  "everyone")
async def help(ia):
    with (open("commands.md") as f):
        await ia.response.send_message(f.read(), ephemeral=True)

@command("admin_help", "command help for admins",  "admin")
async def admin_help(ia):
    with open("admin_commands.md") as f:
        await ia.response.send_message(f.read(), ephemeral=True)

def dss(players, matches, current_round):
    # first calc points etc.
    points = {}
    byes = []
    for player in players:
        points[player] = 0
    for match in matches:
        #undef sweep1 sweep2 corp runner id 2411 2412 tie1 tie2 tietie bye
        try:
            _ = points[match[0]]
        except KeyError:
            points[match[0]] = 0
        try:
            _ = points[match[1]]
        except KeyError:
            points[match[1]] = 0
        if match[3] > current_round - 5:
            match match[2]:
                case 0 | 5:
                    points[match[0]] += 6
                case 1 | 6:
                    points[match[1]] += 6
                case 2 | 3 | 4 | -1:
                    points[match[0]] += 3
                    points[match[1]] += 3
                case 7:
                    points[match[0]] += 4
                    points[match[1]] += 1
                case 8:
                    points[match[0]] += 1
                    points[match[1]] += 4
                case 9:
                    points[match[0]] += 2
                    points[match[1]] += 2
                case 10:
                    points[match[0]] += 6
                    byes.append(match[0])
    rd.shuffle(players)
    players.sort(key=lambda pl: points[pl])
    bye = None
    if len(players)%2 == 1:
        for i in range(len(players)):
            if players[i] not in byes:
                bye = ([players.pop(i), "BYE"])
                break
    edges = [[a, b, 0] for idx, a in enumerate(players) for b in players[idx + 1:]]
    for i, edge in enumerate(edges):
        a, b, _ = edge
        error = 10000
        for match in matches:
            if a in match and b in match:
                error -= max(0, (9-current_round + match[3])*2000)
        error -= (points[a] - points[b]) ** 2
        edges[i] = [players.index(a), players.index(b), error]

    pairings = [[players[i], players[j]] for i, j in enumerate(mwm.maxWeightMatching(edges, True)) if i >= j]
    if bye is not None:
        pairings.append(bye)
    return pairings

@command("cobra_tournament", "Set up a cobra tournament to watch", "admin")
async def cobra_tournament(ia, tournament_id: int):
    cursor.execute('''INSERT INTO cobra_tournaments VALUES (?, ?, ?, ?, ?)''', (tournament_id, ia.channel.id, round(time.time())+7200, 0, ia.guild.id))
    db.commit()
    return await ia.response.send_message(f"The tournament {tournament_id} has been set up. It will check for new rounds until at least <t:{round(time.time())+7200}:t>, but this time is refreshed whenever the cobra changes or you call the `\\activate` command.", ephemeral=True)

@command("activate_tournament", "Activate a timeouted tournament again", "admin")
async def activate_tournament(ia):
    cursor.execute('''UPDATE cobra_tournaments SET active_until=? WHERE channel_id=?''', (round(time.time()+7200), ia.channel.id))
    db.commit()
    return await ia.response.send_message(f"The tournament is active until at least <t:{round(time.time())+7200}:t>.", ephemeral=True)

@command("tournament_pairings", "Get the pairings for the current cobra tournament", "everyone")
async def tournament_pairings(ia):
    cursor.execute('''SELECT tournament_id, round FROM cobra_tournaments WHERE channel_id=?''', (ia.channel_id, ))
    tournaments = cursor.fetchall()
    if len(tournaments) == 0:
        return await ia.response.send_message(f"There is no cobra tournament set up for this channel.", ephemeral=True)
    tournament_id = tournaments[0][0]
    url = f"https://tournaments.nullsignal.games/tournaments/{tournament_id}.json"
    async with aiohttp.ClientSession() as session:
        raw_data = await session.get(url)
    data = await raw_data.json()
    msg = ''
    for pairing in data['rounds'][-1]:
        msg += f"`{pairing['table']}:` {get_player(ia, data['players'], pairing['player2']['id'])} - {get_player(ia, data['players'], pairing['player1']['id'])}\n"
    return await ia.response.send_message(msg, ephemeral=True)

@command("tournament_standings", "Get the standings for the current cobra tournament", "everyone")
async def tournament_standings(ia):
    cursor.execute('''SELECT tournament_id, round FROM cobra_tournaments WHERE channel_id=?''', (ia.channel_id, ))
    tournaments = cursor.fetchall()
    if len(tournaments) == 0:
        return await ia.response.send_message(f"There is no cobra tournament set up for this channel.", ephemeral=True)
    tournament_id = tournaments[0][0]
    url = f"https://tournaments.nullsignal.games/tournaments/{tournament_id}.json"
    async with aiohttp.ClientSession() as session:
        raw_data = await session.get(url)
    data = await raw_data.json()
    msg = '`Pos|Pts|   SoS|  ESoS` - Username\n'
    for player in data['players']:
        msg += f"`{str(player['rank']):>3}|{str(player['matchPoints']):>3}|{(player['strengthOfSchedule']):>6}|{(player['extendedStrengthOfSchedule']):>6}` - {get_player(ia, player_name=player['name'])}\n"
    return await ia.response.send_message(msg, ephemeral=True)

def get_player(ia, players=None, player_id=None, player_name="not found"):
    if players is not None and player_id is not None:
        for player in players:
            if player['id'] == player_id:
                player_name = player['name']
    player = ia.guild.get_member_named(player_name)
    if player is None:
        return player_name
    return player.mention



@command("remove_tournament", "Remove a cobra tournament", "admin")
async def remove_tournament(ia):
    cursor.execute('''DELETE FROM cobra_tournaments WHERE channel_id=?''', (ia.channel_id, ))
    db.commit()
    return await ia.response.send_message("You removed all tournaments in this channel", ephemeral=True)