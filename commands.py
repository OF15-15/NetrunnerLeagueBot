import asyncio
import inspect
import time
import discord
import sqlite3
import functools
import json as js
import random as rd
import mwmatching as mwm

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
    cursor.execute('''INSERT INTO leagues VALUES (?, ?, ?, ?, ?)''', (None, ia.guild_id, ia.channel_id, name, 0))
    db.commit()
    await ia.response.send_message(f"You created league {name} in this channel")


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
async def standings(ia):
    cursor.execute('''SELECT league_id, current_round FROM leagues WHERE channel_id=?''', (ia.channel_id,))
    league_id, current_round = cursor.fetchone()
    cursor.execute('''SELECT pl.user_id FROM player_leagues as pl WHERE pl.league_id=?''', (league_id,))
    players = [p[0] for p in cursor.fetchall()]
    cursor.execute('''SELECT player1_id, player2_id, result, round FROM matches WHERE league_id=?''', (league_id, ))
    matches = cursor.fetchall()
    db.commit()
    points = {player: 0 for player in players}

    for match in matches:
        # sweep1 sweep2 corp runner id 2411 2412 tie1 tie2 tietie bye
        if match[3] > current_round - 5:
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
        msg += f'{ia.guild.get_member(player).mention}: {points[player]}\n'
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
            return await ia.response.send_message(f"Please specify whether the result was id, corp split or runner split in the last argument", ephemeral=True)
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
async def reminder(ia):
    cursor.execute('''SELECT league_id, current_round FROM leagues WHERE channel_id=?''', (ia.channel_id,))
    league_id, current_round = cursor.fetchone()
    print(current_round)
    cursor.execute('''SELECT player1_id, player2_id, result FROM matches WHERE league_id=? and round=?''', (league_id, current_round))
    data = cursor.fetchall()
    msg = ''
    for item in data:
        print(item)
        match item[2]:
            case -1: msg += f'{ia.get_member(item[0]).mention} ? - ? {ia.get_member(item[1]).mention}'
            case 0: msg += f'{ia.get_member(item[0]).name} 6 - 0 {ia.get_member(item[1]).name}'
            case 1: msg += f'{ia.get_member(item[0]).name} 0 - 6 {ia.get_member(item[1]).name}'
            case 2: msg += f'{ia.get_member(item[0]).name} 3 - 3 {ia.get_member(item[1]).name} (C)'
            case 3: msg += f'{ia.get_member(item[0]).name} 3 - 3 {ia.get_member(item[1]).name} (R)'
            case 4: msg += f'{ia.get_member(item[0]).name} 3 - 3 {ia.get_member(item[1]).name} (ID)'
            case 5: msg += f'{ia.get_member(item[0]).name} 6 - 0 {ia.get_member(item[1]).name} (241)'
            case 6: msg += f'{ia.get_member(item[0]).name} 0 - 6 {ia.get_member(item[1]).name} (241)'
            case 7: msg += f'{ia.get_member(item[0]).name} 4 - 1 {ia.get_member(item[1]).name}'
            case 8: msg += f'{ia.get_member(item[0]).name} 1 - 4 {ia.get_member(item[1]).name}'
            case 9: msg += f'{ia.get_member(item[0]).name} 2 - 2 {ia.get_member(item[1]).name}'
            case 10: msg += f'{ia.get_member(item[0]).name} 6 - 0 {"BYE":>21}'
        msg += '\n'
    return await ia.response.send_message(msg, ephemeral=False)




@command("results", "View the last round's results ", "everyone")
async def results(ia, round: str = "current"):
    cursor.execute('''SELECT league_id, current_round FROM leagues WHERE channel_id=?''', (ia.channel_id,))
    league_id, current_round = cursor.fetchone()
    try:
        current_round = int(round)
    except ValueError:
        pass
    print(current_round)
    cursor.execute('''SELECT player1_id, player2_id, result FROM matches WHERE league_id=? and round=?''', (league_id, current_round))
    data = cursor.fetchall()
    msg = ''
    for item in data:
        print(item)
        match item[2]:
            case -1: msg += f'<@{item[0]}> ? - ? <@{item[1]}>'
            case 0: msg += f'<@{item[0]}> 6 - 0 <@{item[1]}>'
            case 1: msg += f'<@{item[0]}> 0 - 6 <@{item[1]}>'
            case 2: msg += f'<@{item[0]}> 3 - 3 <@{item[1]}>'
            case 3: msg += f'<@{item[0]}> 3 - 3 <@{item[1]}>'
            case 4: msg += f'<@{item[0]}> 3 - 3 <@{item[1]}>'
            case 5: msg += f'<@{item[0]}> 6 - 0 <@{item[1]}>'
            case 6: msg += f'<@{item[0]}> 0 - 6 <@{item[1]}>'
            case 7: msg += f'<@{item[0]}> 4 - 1 <@{item[1]}>'
            case 8: msg += f'<@{item[0]}> 1 - 4 <@{item[1]}>'
            case 9: msg += f'<@{item[0]}> 2 - 2 <@{item[1]}>'
            case 10: msg += f'<@{item[0]}> 6 - 0 {"BYE":>21}'
        msg += '\n'
    return await ia.response.send_message(msg, ephemeral=True)


@command("pair", "Pair a new round", "admin")
async def pair(ia):
    cursor.execute('''SELECT league_id, current_round FROM leagues WHERE channel_id=?''', (ia.channel_id,))
    league_id, current_round = cursor.fetchone()
    cursor.execute('''SELECT pl.user_id FROM player_leagues as pl WHERE pl.league_id=?''', (league_id,))
    players = [p[0] for p in cursor.fetchall()]
    cursor.execute('''SELECT player1_id, player2_id, result, round FROM matches WHERE league_id=?''', (league_id, ))
    matches = cursor.fetchall()
    pairings = dss(players, matches, current_round)
    if len(pairings) == 0:
        await ia.response.send_message("league is empty", ephemeral=True)
    msg = ""
    for pairing in pairings:
        if pairing[1] == "BYE":
            msg += f"<@{pairing[0]}>" + " vs BYE\n"
        else:
            msg += f"<@{pairing[0]}> vs <@{pairing[1]}>\n"
        print(pairing)
    current_round += 1
    cursor.execute("""UPDATE leagues SET current_round=? WHERE league_id=?""", (current_round, league_id))
    cursor.executemany('''INSERT INTO matches VALUES (?, ?, ?, ?, ?, ?)''', [(None, league_id, current_round, p1, p2, -1) for p1, p2 in pairings])
    cursor.execute("""UPDATE matches SET result=? WHERE player2_id=?""", (10, 'BYE'))
    db.commit()
    await ia.response.send_message(msg)

@command("help", "command help",  "everyone")
async def help(ia):
    with open("commands.md") as f:
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
            if a == match[0] and b == match[1]:
                error -= max(0, 9-current_round + match[0])*1000
        error -= (points[a] - points[b]) ** 2
        edges[i] = [players.index(a), players.index(b), error]

    pairings = [[players[i], players[j]] for i, j in enumerate(mwm.maxWeightMatching(edges, True)) if i >= j]
    if bye is not None:
        pairings.append(bye)
    return pairings