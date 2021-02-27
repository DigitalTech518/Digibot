import dbl
import discord
from discord.ext import commands
from discord.utils import get


class TopGG(commands.Cog):
	"""Handles interactions with the top.gg API"""

	def __init__(self, bot):
		self.bot = bot
		self.token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6Ijc4MTI5NjcxNzI0NDM5OTYxNyIsImJvdCI6dHJ1ZSwiaWF0IjoxNjA5MTkzMjMwfQ.Fx2ewhQbufkOj7Qp705wBZMPrdCYy3RSInHu0JN2s0E' # set this to your DBL token
		self.dblpy = dbl.DBLClient(self.bot, self.token, autopost=True) # Autopost will post your guild count every 30 minutes

	async def on_guild_post():
		guild = get(discord.guild, id = '781296834777186345')
		channel = get(guild.channels, id = '793239012994318366')
		channel.send("Server Count posted successfully")
		print(guild)
		print(channel)

def setup(bot):
	bot.add_cog(TopGG(bot))