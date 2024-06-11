import asyncio
import inspect
import time
import discord
import sqlite3
import functools
import json as js
import random as rd

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
    cursor.execute('''INSERT INTO leagues VALUES (?, ?, ?, ?)''', (None, ia.guild_id, ia.channel_id, name))
    db.commit()
    await ia.response.send_message(f"You created league {name} in this channel", ephemeral=True)


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
@command("pair", "pair a new round", "admin")
async def pair(ia):
    cursor.execute('''SELECT pl.user_id FROM leagues as l, player_leagues as pl WHERE l.channel_id=? and l.league_id=pl.league_id''', (ia.channel.id,))
    players = [p[0] for p in cursor.fetchall()]
    db.commit()
    rd.shuffle(players)
    msg = ""
    for i in range(0, len(players)-1, 2):
        msg += f"{ia.guild.get_member(players[i]).mention} vs {ia.guild.get_member(players[i+1]).mention}\n"
    if len(players)%2 == 1:
        msg += f"{ia.guild.get_member(players[-1]).mention} vs BYE"
    await ia.response.send_message(msg)