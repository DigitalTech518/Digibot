from discord.ext import commands
import requests
import discord
from datetime import datetime, timedelta, time
try:
	from Bot import sendMessage, sendLog, writeFile, openFile
except:
	from Bot1 import sendMessage, sendLog, writeFile, openFile

class User(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(aliases = ["avatar","profile_picture"])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def pfp(self, ctx, member: discord.Member = None):
		await ctx.trigger_typing()
		if member == None:
			member = ctx.message.author
		avatar = member.avatar_url_as(static_format = "png")
		embed = discord.Embed(color = int("03fcf0" , 16))
		embed.set_author(name=member.name, icon_url=avatar)
		embed.set_image(url = avatar)
		time = str(datetime.now()).split(".")[0]
		time = str(time).split(" ")[1]
		embed.set_footer(text = f"{ctx.author.name} requested command at {time}")
		await ctx.message.reply(mention_author = False, embed = embed)
	
	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def profile(self, ctx, member: discord.Member = None):
		await ctx.trigger_typing()
		if member == None:
			member = ctx.message.author
		if len(member.roles) == 1:
			memberRole = "No Roles"
		else:
			memberRole = member.roles[-1].mention
		embed = discord.Embed(title = f"{member.name}#{member.discriminator}", color = ctx.bot.embedColor)
		embed.add_field(name = "Nickname", value = member.nick)
		embed.add_field(name = "Join Date", value = str(member.joined_at).split(' ')[0])
		embed.add_field(name = "Account Creation", value = str(member.created_at).split(' ')[0])
		embed.add_field(name = "Highest Role", value = memberRole)
		time = str(datetime.now()).split(".")[0]
		time = str(time).split(" ")[1]
		embed.set_footer(text = f"{ctx.author.name} requested command at {time}")
		await ctx.message.reply(mention_author = False, embed = embed)

def setup(bot):
	bot.add_cog(User(bot))