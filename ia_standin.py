import discord

class Interaction:
    def __init__(self, guild_id, channel_id, user_id, client, ephemeral=False):
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.user_id = user_id
        self.guild = client.get_guild(guild_id)
        self.channel = self.guild.get_channel(channel_id)
        self.user = self.guild.get_member(user_id)
        self.response = Messenger(self)
        self.followup = Messenger(self)
        self.ephemeral = ephemeral

class Messenger:
    def __init__(self, ia):
        self.ia = ia
    async def send_message(self, message, ephemeral=False, **kwargs):
        if not message:
            message = "some error"
        await self.ia.channel.send(content=message, silent=ephemeral and self.ia.ephemeral, **kwargs)
    async def send(self, *args, **kwargs): await self.send_message(*args, **kwargs)
    async def defer(self, *args, **kwargs): return None