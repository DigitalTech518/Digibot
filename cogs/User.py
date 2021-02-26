from discord.ext import commands
import requests
import discord
from datetime import datetime, timedelta, time
import motor.motor_asyncio
try:
	from Bot import sendMessage, sendLog, writeFile, openFile, pagination
except:
	from Bot1 import sendMessage, sendLog, writeFile, openFile, pagination

class User(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(aliases = ["avatar","profile_picture"])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def pfp(self, ctx, member: discord.Member = None):
		def createSizes(member, extension):
  			sizes = [128, 256, 512, 1024]
  			string = ""
  			for size in sizes:
  			  string += f"[{size}x]({member.avatar_url_as(format=(extension), size=size)}) "
  			return string
		if member == None:
			member = ctx.message.author
		avatar = str(member.avatar_url_as(format=("gif" if member.is_avatar_animated() else "png")))
		extensions = ["gif", "png", "jpeg", "jpg", "webp"] if avatar.find("gif") != -1 else [ "png", "jpeg", "jpg", "webp"]
		avatarEmbeds = []
		for extension in extensions:
			embed = discord.Embed(color=self.bot.embedColor, title=f"{member.name}\'s avatar", description=f"`{extension.upper()}`\n{createSizes(member, extension)}")
			embed.set_image(url=member.avatar_url_as(format=(extension), size=2048))
			avatarEmbeds.append(embed)
		await pagination(ctx.message, avatarEmbeds, True)
	
	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def profile(self, ctx, member: discord.Member = None):
		await ctx.trigger_typing()
		if member == None:
			member = ctx.message.author
		cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
		Users = cluster["bot"]["Users"]
		doc = await Users.find_one({"_id": str(member.id)})
		wins = None
		looses = None
		if doc:
			if "rouletteWins" in doc:
				wins = doc["rouletteWins"]
			if "rouletteLooses" in doc:
				looses = doc["rouletteLooses"]
		if len(member.roles) == 1:
			memberRole = "No Roles"
		else:
			memberRole = member.roles[-1].mention
		embed = discord.Embed(title = f"{member.name}#{member.discriminator}", color = ctx.bot.embedColor)
		embed.add_field(name = "Nickname", value = member.nick)
		embed.add_field(name = "Join Date", value = str(member.joined_at).split(' ')[0])
		if not wins == None:
			embed.add_field(name = "Roulette Wins", value = wins)
		if wins == None:
			embed.add_field(name = "Roulette Wins", value = 0)
		if not looses == None:
			embed.add_field(name = "Roulette Losses", value = looses)
		if looses == None:
			embed.add_field(name = "Roulette Losses", value = 0)
		embed.add_field(name = "Account Creation", value = str(member.created_at).split(' ')[0])
		embed.add_field(name = "Highest Role", value = memberRole)
		time = str(datetime.now()).split(".")[0]
		time = str(time).split(" ")[1]
		embed.set_footer(text = f"{ctx.author.name} requested command at {time}")
		await ctx.message.reply(mention_author = False, embed = embed)

def setup(bot):
	bot.add_cog(User(bot))