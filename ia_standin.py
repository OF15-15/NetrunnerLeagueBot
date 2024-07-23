import discord

class Interaction:
    def __init__(self, guild_id, channel_id, user_id, client):
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.user_id = user_id
        self.guild = client.get_guild(guild_id)
        self.channel = self.guild.get_channel(channel_id)
        self.user = self.guild.get_member(user_id)
        self.response = Messenger(self)

class Messenger:
    def __init__(self, ia):
        self.ia = ia
    async def send_message(self, message, ephemeral=False, **kwargs):
        await self.ia.channel.send(content=message, silent=ephemeral, **kwargs)