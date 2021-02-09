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
	from Bot import sendMessage, sendLog, writeFile, openFile
except:
	from Bot1 import sendMessage, sendLog, writeFile, openFile

with open("config.json") as jsonFile:
	data = load(jsonFile)
botPrefix = data["prefix"]

class BOT(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(aliases = ["suggest"])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def github(self, ctx):
		await ctx.trigger_typing()
		await sendMessage(ctx, "Want to contribute, or let me know about an error?", "Click [here](https://github.com/DigitalTech518/Digibo) to go to my github!")

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def vote(self, ctx):
		await ctx.trigger_typing()
		await sendMessage(ctx, "Vote if you like Digibot!", "Click [here](https://voidbots.net/bot/781296717244399617/) or [here](https://top.gg/bot/781296717244399617#/) if you like Digibot and want to vote for it!")

	@commands.command()
	@commands.guild_only()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def support(self,ctx, *, message): 
		await ctx.trigger_typing()
		channel = ctx.bot.get_channel(798389844433829888)
		await sendMessage(channel, f"Support Requested!\n**UserID:** {ctx.message.author.id}\n**Username:** {ctx.message.author.name}#{ctx.message.author.discriminator}", f"**Message:** {str(message)}", message = "<@577640430683029514>")
		await sendMessage(ctx, "Message has been sent!", "You'll recieve support as soon as possible.")
	
	@commands.command(aliases = ["list"])
	@commands.cooldown(1, 1.5, commands.BucketType.user)
	async def help(self, ctx, category = None):
		await ctx.trigger_typing()
		data = requests.get("https://raw.githubusercontent.com/DigitalTech518/Digibot/main/help.json")
		if category == None:
			categories = []
			for categoryy in data.json()["help"]:
				categories.append(str(categoryy))
			categoryList = "\n".join(categories)
			await sendMessage(ctx, "Categories", categoryList, footer = "Do d!help [category] to look at categories or d!help [command] for more info on a command!")
			return
		category = category.lower()
		categoryName = []
		if str(category) in data.json()["categories"]:
			for commandName in data.json()["categories"][category]["commands"]:
				categoryName.append(commandName)
			categoryName = "\n".join(categoryName)
			await sendMessage(ctx, category, f"**```{str(categoryName)}```**")
		if not str(category) in data.json()["categories"]:
			commandName = data.json()["commands"][category]
			embed = discord.Embed(title = category, color = ctx.bot.embedColor)
			for key in data.json()["commands"][category]:
				embed.add_field(name = key, value = data.json()["commands"][category][key], inline = False)
			embed.set_footer(text = "Do d!help [category] to look at categories or d!help [command] for more info on a command!")
			await ctx.send(embed = embed)
	
	@commands.command(aliases = ["latency"])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def ping(self, ctx):
		await ctx.trigger_typing()
		await sendMessage(ctx, f"Pong! The latency is {round(ctx.bot.latency * 1000)}ms")
	
	@commands.command()
	@commands.has_permissions(manage_roles = True)
	@commands.guild_only()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def prefix(self, ctx, *, prefix = botPrefix):
		await ctx.trigger_typing()
		data = await openFile("files/customprefix")
		guildID = str(ctx.guild.id)
		if prefix == botPrefix:
			data.pop(guildID, None)
		else:
			data[guildID] = prefix
		outFile = await writeFile("files/customprefix", data)
		await sendMessage(ctx, "Prefix has been changed to:", prefix)
		try:
			await sendMessage(await getLog(ctx.guild.id, "server"), "Prefix was changed.", f"Prefix was changed to {prefix}", None, f"Moderator Responsible: {ctx.author.id}")
		except:
			pass

	@commands.command(aliases = ["botinfo"])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def info(self, ctx):
		await ctx.trigger_typing()
		embed = discord.Embed(color = ctx.bot.embedColor, title = "Bot info")
		try:
			test = await openFile("files/customprefix")
			embed.add_field(name = "**Server** Prefix", value = test[str(ctx.guild.id)])
		except:
			embed.add_field(name = "**Server** Prefix", value = botPrefix)
		embed.add_field(name = "Default Prefix", value = botPrefix)
		current_time = datetime.now()
		difference = current_time - ctx.bot.start_time
		uptime = str(difference).split(".")[0]
		embed.add_field(name = "Uptime", value = uptime)
		embed.add_field(name = "Color", value = ctx.bot.embedColor)
		embed.add_field(name = "Server Count", value = len(ctx.bot.guilds))
		userCount = 0
		for guild in ctx.bot.guilds:
			Int = int(len(guild.members))
			userCount = userCount + Int 
		embed.add_field(name = "Amount of Users", value = userCount)
		embed.add_field(name = "Launches", value = ctx.bot.launches)
		embed.add_field(name = "Discord", value = "Join my server! https://discord.gg/9G9vf6qvdH")
		embed.set_footer(text = "Bot made by Digital_Tech")
		await ctx.message.reply(embed = embed)

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def invite(self, ctx):
		await ctx.trigger_typing()
		await sendMessage(ctx, None, "Click [here](https://discord.com/oauth2/authorize?client_id=781296717244399617&permissions=8&scope=bot) to invite my bot!")

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def stats(self, ctx, command = None):
		await ctx.trigger_typing()
		data = await openFile("files/stats")
		if command != None:
			stats = data["Commands"][command]
			await sendMessage(ctx, f"The number of uses for {command}:", stats)
			return
		commandList = []
		for item in data["Commands"]:
			commandList.append((item, data["Commands"][item]))
		commandList.sort(key = lambda x:x[1])
		commandList.reverse()
		top5gaming = []
		for x in range(5):
			try:
				top5gaming.append(f"{x + 1}. **{commandList[x][0]} - {commandList[x][1]}**")
			except:
				break
		await sendMessage(ctx, "Top 5 Commands", "\n".join(top5gaming))
	
	@commands.command()
	@commands.has_permissions(manage_roles = True)
	@commands.guild_only()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def disablecommand(self, ctx, command):
		try:
			await ctx.trigger_typing()
		except:
			pass
		data = await openFile("files/disabledCommands")
		try:
			guild = ctx.guild
		except:
			guild = ctx
		command = self.bot.get_command(command)
		guildID = str(guild.id)
		if command == None:
			try:
				await sendMessage(ctx, "That is an invalid command")
			except:
				pass
			return
		if str(command) in ["disablecommand", "help", "privacy"]:
			try:
				await sendMessage(ctx, "This command can't be disabled.")
			except:
				pass
			return
		try:
			if str(command) in data[guildID]["commands"]:
				try:
					await sendMessage(ctx, "This command is already disabled!")
				except:
					pass
				return
		except:
			pass
		if not guildID in data:
			data[guildID] = {}
		if not "commands" in data[guildID]:
			data[guildID]["commands"] = []
		if not str(command) in data[guildID]["commands"]:
			data[guildID]["commands"].append(str(command))
		try:
			await sendMessage(ctx, "Command has been disabled", f"`{command}` has been disabled for {guild.name}.")
		except:
			pass
		outFile = await writeFile("files/disabledCommands", data)
	
	@commands.command()
	@commands.has_permissions(manage_roles = True)
	@commands.guild_only()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def enablecommand(self, ctx, command):
		try:
			await ctx.trigger_typing()
		except:
			pass
		data = await openFile("files/disabledCommands")
		guildID = str(ctx.guild.id)
		if command != "invalidCommand":
			commandName = ctx.bot.get_command(command)
		if command == "invalidCommand":
			commandName = "invalidCommand"
		if not str(commandName) in data[guildID]["commands"]:
			await sendMessage(ctx, "This command isn't disabled!")
			return
		data[guildID]["commands"].remove(str(commandName))
		await sendMessage(ctx, f"{command} has been enabled.")
		outFile = await writeFile("files/disabledCommands", data)


	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def privacy(self, ctx):
		await ctx.trigger_typing()
		embed = discord.Embed(title = "Privacy Policy", color = ctx.bot.embedColor)
		embed.add_field(name = "What data do we store?", value = "The only data the bot stores is guild IDs and member IDs. This is used for guild specific commands like prefix, or member specific commands like time or reminder. I also store some simple guild info when you invite the bot to your server. This info is shown to no one execpt myself.")
		embed.add_field(name = "How long do we keep it?", value = "The guild ID data is stored untill you kick the bot out of the server. Member ID data is stored, in some cases permanently.")
		embed.add_field(name = "How can I remove it?", value = "Use the command d!support to contact me or even directly dm me if possible, and I will remove it manually. Use this command to contact me with any concerns as well.")
		embed.add_field(name = "Why do we store this data?", value = "We store this data for a couple reasons. Guild IDs are stored for commands like disabledcommand, so commands are disabled for that certain guild. Member IDs are stored for member specfic things, like a reminder thats meant to dm that specific user.")
		await ctx.send(embed = embed)

def setup(bot):
	bot.add_cog(BOT(bot))