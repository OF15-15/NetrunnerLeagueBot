import asyncio
import inspect
import time
import discord
import sqlite3
import functools
import json as js

command_list = []
with open("data.json") as f:
    guilds_data = js.load(f)


def command(name, description, perms):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(ia, *args, **kwargs):
            if perms == "everyone":
                pass
            elif auth_admin(ia.guild, ia.user):
                pass
            else:
                return await ia.response.send_message(f"Du darfst diesen Befehl nicht benutzen", ephemeral=True)
            await func(ia, *args, **kwargs)

        command_list.append(discord.app_commands.Command(callback=wrapper, name=name, description=description))
        return wrapper
    return decorator

"""
@command("echo", "Echo the string put in", ["admin"], ["admin"])
async def echo(ia, content: str):
    await ia.response.send_message(content)
"""

db: sqlite3.Connection
cursor: sqlite3.Cursor


def auth_admin(guild, user):
    cursor.execute('''SELECT admin_id FROM admins WHERE guild_id = ? AND admin_id=?''', (guild, user))
    owner = cursor.fetchone()
    db.commit()
    if owner is None:
        return False
    return True
