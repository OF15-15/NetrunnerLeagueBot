import discord

class Interaction:
    def __init__(self, guild_id, channel_id, user_id):
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.user_id = user_id
        self.guild = discord.Object(id=guild_id)
        self.channel = discord.Object(id=channel_id)
        self.user = discord.Object(id=user_id)
        self.response = Messenger(self)

class Messenger:
    def __init__(self, ia):
        self.ia = ia
    def send_message(self, message, ephemeral=False, **kwargs):
        self.ia.channel.send(content=message, silent=ephemeral, **kwargs)