from datetime import datetime, timedelta, time
from discord.ext import commands
from json import load, dumps
from asyncio import sleep
import requests
from re import search
import discord
import random
from discord.utils import get
from os import listdir
from platform import system
try:
	from Bot import sendMessage, getLog, sendLog, writeFile, openFile
except:
	from Bot1 import sendMessage, getLog, sendLog, writeFile, openFile

class Server(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	@commands.guild_only()
	@commands.has_permissions(manage_roles = True)
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def setjoinrole(self, ctx, *, role):
		await ctx.trigger_typing()
		Role = discord.utils.get(ctx.guild.roles, name = role)
		if Role == None:
			await sendMessage(ctx, f"{role} is an invalid role!")
			return
		data = await openFile("files/joinroles")
		guildID = str(ctx.guild.id)
		if guildID in data:
			if role in data[guildID]:
				await sendMessage(ctx, "That role has already been set as a join role!")
				return
		if not guildID in data:
			data[guildID] = []
		data[guildID].append(role) 
		outFile = await writeFile("files/joinroles", data)
		await sendMessage(ctx, f"{role} has been set as a join role!")
		embed = discord.Embed(title = "Join role has been set.", description = f"The join role `{role}` has been set as a join role.", color = ctx.bot.embedColor)
		await sendLog(ctx.guild.id, "server", embed)
	
	@commands.command()
	@commands.has_permissions(manage_roles = True)
	@commands.guild_only()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def viewjoinroles(self, ctx):
		await ctx.trigger_typing()
		data = await openFile("files/joinroles")
		guildID = str(ctx.guild.id)
		if not guildID in data:
			await sendMessage(ctx, "You have no join roles setup!")
			return
		List = []
		for roles in data[guildID]:
			List.append(roles)
		betterList = "\n".join(List)
		await sendMessage(ctx, "Join Roles", f"**{betterList}**")
	
	@commands.command()
	@commands.has_permissions(manage_roles = True)
	@commands.guild_only()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def removejoinrole(self, ctx, *, roleNum):
		await ctx.trigger_typing()
		roleNum = int(roleNum) - 1
		data = await openFile("files/joinroles")
		guildID = str(ctx.guild.id)
		if not guildID in data:
			await sendMessage(ctx, "You have no join roles setup!")
			return
		if not guildID in data:
			await sendMessage(ctx, "You have no join roles setup!")
			return
		if len(data[guildID]) < 1:
			data.pop(guildID)
			await sendMessage(ctx, "You have no join roles setup!")
		else:
			data[guildID].pop((roleNum))
			if len(data[guildID]) < 1:
				data.pop(guildID)
			await sendMessage(ctx, f"Join role {int(roleNum) + 1} has been removed.")
		outFile = await writeFile("files/joinroles", data)
	
	@commands.command()
	@commands.has_permissions(manage_channels = True)
	@commands.guild_only()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def removelogs(self, ctx, channel: discord.TextChannel, category = None):
		await ctx.trigger_typing()
		if category == None:
			category = "general"
		data = await openFile("files/auditlog")
		guildID = str(ctx.guild.id)
		del(data[category][guildID])	
		await sendMessage(ctx, f"Audit has been removed from {channel.name}.")
		await sendMessage(await getLog(ctx.guild.id, "server"), f"Audit has been removed from {channel.name}.")
		outFile = await writeFile("files/auditlog", data)

	@commands.command(aliases = ["slow"])
	@commands.has_permissions(manage_channels = True)
	@commands.guild_only()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def slowmode(self, ctx, time = None):
		await ctx.trigger_typing()
		if time == None:
			time = "0s"
		m = search(r"([\d.]+)([smhdw]?)", time)
		time = float(m.group(1))
		length = m.group(2)
		if length == "":
			length = "s"
		if length == "s":
			finaltime = time
		elif length == "h":
			finaltime = time * 3600
		else:
			finaltime = time
		channel = ctx.channel
		moderator = ctx.author.id
		await channel.edit(slowmode_delay = finaltime)
		await sendMessage(ctx, f"Slowmode delay has been set to {finaltime}", None, None, f"Moderator responsible: {moderator}")
	
	@commands.command(aliases = ["sinfo"])
	@commands.guild_only()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def serverinfo(self, ctx):
		await ctx.trigger_typing()
		embed = discord.Embed(title = "Server Info", color = ctx.bot.embedColor, description = ctx.guild.name)
		embed.add_field(name = "Owner", value = ctx.guild.owner)
		embed.add_field(name = "Member Count", value = ctx.guild.member_count)
		roles = ""
		for i in ctx.guild.roles:
			roles += i.mention + " "
		if len(roles.split(" ")) <= 35:
			embed.add_field(name = "Server Roles", value = roles)
		else:
			embed.add_field(name = "Amount of Server Roles", value = len(roles.split(" ")) - 1)
		embed.add_field(name = "Max File Size", value = ctx.guild.filesize_limit / 1e+6)
		embed.add_field(name = "Booster Level", value = ctx.guild.premium_tier)
		embed.add_field(name = "Amount of Boosters", value = ctx.guild.premium_subscription_count)
		time = str(datetime.now()).split(".")[0]
		time = str(time).split(" ")[1]
		embed.set_footer(text = f"{ctx.author.name} requested command at {time}")
		await ctx.message.reply(mention_author = False, embed = embed)


	@commands.command()
	@commands.has_permissions(manage_channels = True)
	@commands.guild_only()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def lock(self, ctx, channel:discord.TextChannel = None):
		await ctx.trigger_typing()
		if channel == None:
			channel = ctx.channel
		await channel.set_permissions(ctx.guild.default_role, send_messages = False)
		await sendMessage(ctx, f"{channel} Locked")
		try:
			await sendMessage(await getLog(ctx.guild.id, "moderation"), "Channel was locked.", f"{channel} was locked", None, f"Moderator Responsible: {ctx.author.id}")
		except:
			pass
	
	@commands.command()
	@commands.has_permissions(manage_channels = True)
	@commands.guild_only()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def unlock(self, ctx, channel:discord.TextChannel = None):
		await ctx.trigger_typing()
		if channel == None:
			channel = ctx.channel
		await channel.set_permissions(ctx.guild.default_role, send_messages = None)
		await sendMessage(ctx, f"{channel} Unlocked")
		try:
			await sendMessage(await getLog(ctx.guild.id, "moderation"), "Channel was unlocked.", f"{channel} was unlocked", None, f"Moderator Responsible: {ctx.author.id}")
		except:
			pass

	@commands.command()
	@commands.has_permissions(manage_channels = True)
	@commands.guild_only()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def setlogs(self, ctx, channel:discord.TextChannel, category = None):
		await ctx.trigger_typing()
		if category == None:
			category = "general"
		else:
			category == category.lower()
		with open("files/auditlog.json") as jsonFile:
			data = load(jsonFile)
		if not category in data:
			newLine = "`\n`"
			await sendMessage(ctx, "Avaliable categories:", f"`**{newLine.join(data.keys())}**`")
			return
		guildID = (ctx.guild.id)
		if not guildID in data[category]:
			data[category][guildID] = {}
		data[category][guildID] = (channel.id)
		with open("files/auditlog.json", "w") as outFile:
			outFile.write(dumps(data, indent = 2))		
		await sendMessage(ctx, f"Auditlog ({category}) has been set to {channel}.")
		try:
			await sendMessage(await getLog(ctx.guild.id, "server"), "Audit Log was set", f"{category} was set to {channel}.", None, f"Moderator Responsible: {ctx.author.id}")
		except:
			pass

def setup(bot):
	bot.add_cog(Server(bot))