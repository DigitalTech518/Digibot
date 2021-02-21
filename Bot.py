from datetime import datetime, timedelta, time
from discord.ext import commands, tasks
from json import load, dumps
from asyncio import sleep, get_event_loop, TimeoutError
import requests
from re import search
import discord
import random
from discord.utils import get
from os import listdir
from platform import system
import ibl
import logging
import motor.motor_asyncio
from threading import Thread
from functools import partial
from flask import Flask, render_template
app = Flask( 
    __name__,
    template_folder='templates'
)

global muteLoopRunning
muteLoopRunning = False
global remindLoopRunning
remindLoopRunning = False
#########################################################################################################################

with open("config.json") as jsonFile:
	data = load(jsonFile)

token = data["tokens"]["botToken"]
voidToken = data["tokens"]["voidToken"]
spaceToken = data["tokens"]["spaceToken"]
botPrefix = data["prefix"]
intents = discord.Intents.all()
client = commands.Bot(command_prefix = commands.when_mentioned_or(botPrefix), intents = intents)
client.token = data["tokens"]["botToken"]
client.voidToken = data["tokens"]["voidToken"]
client.spaceToken = spaceToken
client.botPrefix = data["prefix"]
client.embedColor = int(data["colors"]["embedColor"], 16)
embedColor = int(data["colors"]["embedColor"], 16)
client.strColor = data["colors"]["embedColor"]
strColor = client.strColor
client.mutedColor = int(data["colors"]["mutedColor"], 16)
mutedColor = int(data["colors"]["mutedColor"], 16)
data["launches"] = data["launches"] + 1
client.launches = data["launches"]
start_time = datetime.now()
client.start_time = datetime.now()
client.songQueue = {}
client.playedSongs = {}
client.eventLoop = get_event_loop()
client.test = {}
client.Playloop = {}
with open("config.json", "w") as outFile:
	outFile.write(dumps(data, indent = 2))

client.remove_command("help")

#########################################################################################################################

async def sendMessage(ctx, title = None, description = None, colour = None, footer = None, message = None):
	if colour == None:
		try:
			data = await openFile("files/colors")
			if str(ctx.guild.id) in data:
				colour = int(data[str(ctx.guild.id)]["color"], 16)
			else:
				colour = embedColor
		except:
			colour = embedColor
	embed = discord.Embed(title = title, color = colour, description = description)
	if not footer == None:
		embed.set_footer(text = footer)
	if footer == None:
		time = str(datetime.now()).split(".")[0]
		time = str(time).split(" ")[1]
		try:
			embed.set_footer(text = f"{ctx.author.name} requested command at {time}")
		except:
			pass
	try:
		if not message == None:
			await ctx.send.reply(message, mention_author = False, embed = embed)
			return
		await ctx.message.reply(mention_author = False, embed=embed)
	except:
		if not message == None:
			await ctx.send(message, embed = embed)
			return
		await ctx.send(embed = embed)	

async def pagination(message, messages, showpages):
	if showpages == True:
		for demessage in messages:
			demessage.set_footer(text=f"{messages.index(demessage)+1}/{len(messages)}")
	page = 0
	pages = messages
	reactions = ["⏪", "◀️","⏹️", "▶️", "⏩"] if len(messages) > 1 else ["⏹️"]
	mainMessage = await message.channel.send(embed=pages[page])
	for emoji in reactions:
		await mainMessage.add_reaction(emoji)
	incol = True
	while incol == True:
		try:
			collector = await client.wait_for(
						'raw_reaction_add',
						check=(
							lambda x: x.message_id == mainMessage.id
							and x.user_id == message.author.id
							and x.emoji.name in reactions
						),
						timeout=60
					)
			if collector.emoji.name == "⏪":
				page = 0
				try:
					await mainMessage.remove_reaction("⏪", message.author)
				except:
					pass
			elif collector.emoji.name == "◀️":
				if page == 0:
					page = len(messages) - 1
				else: page -= 1
				try:
					await mainMessage.remove_reaction("◀️", message.author)
				except:
					pass
			elif collector.emoji.name == "▶️":
				if page == len(messages) - 1:
					page = 0
				else: page += 1
				try:
					await mainMessage.remove_reaction("▶️", message.author)
				except:
					pass
			elif collector.emoji.name == "⏩":
				page = len(messages)-1
				try:
					await mainMessage.remove_reaction("⏩", message.author)
				except:
					pass
			elif collector.emoji.name == "⏹️":
				incol = False
				try:
					await mainMessage.remove_reaction("⏹️", message.author)
				except:
					pass
				for emoji in reactions:
					await mainMessage.remove_reaction(emoji, client.user)
			await mainMessage.edit(embed=pages[page])
		except TimeoutError:
			incol = False
			for emoji in reactions:
				try:
					await mainMessage.remove_reaction(emoji, client.user)
					await mainMessage.remove_reaction(emoji, message.author)
				except:
					pass

async def sendLog(guildID, category, embed):
	with open("files/auditlog.json") as jsonFile:
		data = load(jsonFile)
	guildID = str(guildID)
	if guildID in data[category]:
		channel = client.get_channel(data[category][guildID])
	else:
		try:
			channel = client.get_channel(data["general"][guildID])
		except:
			return
	await channel.send(embed = embed)

async def getLog(guildID, category):
	with open("files/auditlog.json") as jsonFile:
		data = load(jsonFile)
	guildID = str(guildID)
	if guildID in data[category]:
		channel = client.get_channel(data[category][guildID])
	else:
		try:
			channel = client.get_channel(data["general"][guildID])
		except:
			return
	return channel

async def sendDM(member, title = None, description = None, footer = None):
	embed = discord.Embed(title = title, color = embedColor, description = description)
	if not footer == None:
		embed.set_footer(text = footer)
	try:
		await member.send(embed=embed)
	except:
		pass

async def removeMutes():
	cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
	Guilds = cluster["bot"]["Guilds"]
	cursor = Guilds.find({})
	async for doc in cursor:
		guildID = doc["_id"]
		if "Mutes" in doc:
			if "activeMutes" in doc["Mutes"]:
				for memberID in doc["Mutes"]["activeMutes"]:
					if not len(doc["Mutes"]["activeMutes"][memberID]) < 1:
						mute = doc["Mutes"]["activeMutes"][memberID]
						endTime = datetime.strptime(mute["time"],"%Y-%m-%d %H:%M:%S")
						if datetime.now() > endTime:
							channelID = mute["channelID"]
							channel = client.get_channel(int(channelID))
							guild = client.get_guild(int(guildID))
							muteRole = get(guild.roles, name = "Muted")
							member = guild.get_member(int(memberID))
							await channel.send(f"{member.mention} has been unmuted.")
							await member.remove_roles(muteRole)
							doc["Mutes"]["activeMutes"][memberID] = {}
							await Guilds.find_one_and_update({"_id": guildID}, {"$set": doc})
				if "acitveMutes" in doc["Mutes"]:
					if len(doc["Mutes"]["activeMutes"][memberID]) < 1:
						doc["Mutes"]["activeMutes"].pop(memberID)
					if len(doc["Mutes"]["activeMutes"]) < 1:
						doc["Mutes"].pop("activeMutes")
				await Guilds.find_one_and_update({"_id": guildID}, {"$set": doc})

async def muteLoopStart():
	global muteLoopRunning
	if muteLoopRunning == True:
		muteLoopRunning = False
	else:
		await muteLoop()

async def muteLoop():
	global muteLoopRunning
	muteLoopRunning = True
	while True:
		cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
		Guilds = cluster["bot"]["Guilds"]
		cursor = Guilds.find({})
		closestTime = None
		async for doc in cursor:
			if "Mutes" in doc:
				if "activeMutes" in doc["Mutes"]:
					for memberID in doc["Mutes"]["activeMutes"]:
						if len(doc["Mutes"]["activeMutes"][memberID]) < 1:
							pass
						else:
							time = datetime.strptime(doc["Mutes"]["activeMutes"][memberID]["time"],"%Y-%m-%d %H:%M:%S")
							if closestTime is None or time < closestTime:
								closestTime = time
		if closestTime == None:
			muteLoopRunning = False
			return
		time_delta = (closestTime - datetime.now())
		total_time = time_delta.total_seconds()
		counter = 0
		while muteLoopRunning == True:
			await sleep(1)
			counter += 1
			if counter >= total_time:
				await removeMutes()
				break
		if muteLoopRunning == False:
			muteLoopRunning = True

async def removeRemind():
	cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
	Users = cluster["bot"]["Users"]
	cursor = Users.find({})
	async for doc in cursor:
		memberID = doc["_id"]
		x = -1
		if "reminders" in doc:
			for reminder in doc["reminders"]:
				x = x + 1
				reason = reminder["reason"]	
				endTime = datetime.strptime(reminder["time"],"%Y-%m-%d %H:%M:%S")
				if datetime.now() > endTime:
					if "finaltime" in reminder:
						channelID = reminder["channelID"]
						channel = client.get_channel(int(channelID))
						member = client.get_user(int(memberID))
						finaltime = reminder["finaltime"]
						doc["reminders"].remove(doc["reminders"][int(x)])
						await Users.find_one_and_update({"_id": memberID}, {"$set": doc})
						try:
							await sendMessage(member, "Repeating Reminder", reason, footer = "Use d!reminders to view reminder, and d!removereminder to remove it")
						except:
							await sendMessage(channel, "Reminder", reason, footer = "Use d!reminders to view reminder, and d!removereminder to remove it", message = member.mention)
						await Users.find_one_and_update({"_id": memberID},{
							"$addToSet":{
								"reminders":{
									"time": str(datetime.now()  + timedelta(seconds = finaltime)).split(".")[0],
									"channelID": channel.id,
									"reason": reason,
									"finaltime": finaltime
							}}})
					else:
						try:
							channelID = reminder["channelID"]
							channel = client.get_channel(int(channelID))
							member = client.get_user(int(memberID))
							try:
								await sendMessage(member, "Reminder", reason)
							except:
								await sendMessage(channel, "Reminder", reason, message = member.mention)
						except:
							pass
						doc["reminders"].remove(doc["reminders"][int(x)])
						await Users.find_one_and_update({"_id": memberID}, {"$set": doc})

async def remindLoopStart():
	global remindLoopRunning
	if remindLoopRunning == True:
		remindLoopRunning = False
	else:
		await remindLoop()

async def remindLoop():
	global remindLoopRunning
	remindLoopRunning = True
	while True:
		cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
		Users = cluster["bot"]["Users"]
		cursor = Users.find({})
		closestTime = None
		async for doc in cursor:
			if "reminders" in doc:
				for k in doc["reminders"]:
					time = datetime.strptime(k["time"],"%Y-%m-%d %H:%M:%S")
					if closestTime is None or time < closestTime:
						closestTime = time
		if closestTime == None:
			remindLoopRunning = False
			return
		time_delta = (closestTime - datetime.now())
		total_time = time_delta.total_seconds()
		counter = 0
		while remindLoopRunning == True:
			await sleep(1)
			counter += 1
			if counter >= total_time:
				await removeRemind()
				break
		if remindLoopRunning == False:
			remindLoopRunning = True

async def openFile(file):
	with open(f"{file}.json") as jsonFile:
		return load(jsonFile)

async def writeFile(file, fileData):
	with open(f"{file}.json", "w") as outFile:
		outFile.write(dumps(fileData, indent = 2))

#########################################################################################################################

@client.event
async def on_ready():
	print('Digibot Ready')
	await client.change_presence(activity = discord.Activity(name = f"to {len(client.guilds)} servers. d!help", type = discord.ActivityType.listening))
	await remindLoopStart()
	await muteLoopStart()
	client.statusRefreash.start()
	client.statusRefreash.add_exception_type(asyncpg.PostgresConnectionError)

@tasks.loop(minutes = 30)
async def statusRefreash():
	await client.wait_until_ready()
	await client.change_presence(activity = discord.Activity(name = f"to {len(client.guilds)} servers. d!help", type = discord.ActivityType.listening))

partial_run = partial(app.run, host="0.0.0.0", debug=False, use_reloader=False)
@app.route("/")
def base_page():
	userCount = 0
	for guild in client.guilds:
		userCount += len(guild.members)
	guildCount = len(client.guilds)
	current_time = datetime.now()
	difference = current_time - client.start_time
	uptime = str(difference).split(".")[0]
	return render_template("index.html",
		Users = userCount,
		Guilds = guildCount,
		Uptime = uptime,
		Launches = client.launches,
		Color = strColor,
		CommandCount = len(client.commands)
		)

for filename in listdir('./cogs'):
	if filename.endswith('.py'):
		client.load_extension(f'cogs.{filename[:-3]}')

for filename in listdir('./files'):
	if filename.endswith('.py'):
		client.load_extension(f'files.{filename[:-3]}')

#if not system() == "Windows":
	#client.load_extension(f"files.gg")
	#client.load_extension(f"files.StatsUpload")

@client.event
async def on_message(message):
	if message.author.bot:
		return
	with open("files/customprefix.json") as jsonFile:
			data = load(jsonFile)
	if message.guild != None:
		if str(message.guild.id) in data:
			guildID = str(message.guild.id)
			customPrefix = data[guildID]
			if message.content.startswith(botPrefix) and not "help" in message.content.split(" ")[0] and not "prefix" in message.content.split(" ")[0] and not "botinfo" in message.content.split(" ")[0] and not "info" in message.content.split(" ")[0]:
				message.content = message.content.replace(botPrefix, " ", 1)
			if message.content.startswith(customPrefix):
				message.content = message.content.replace(customPrefix, botPrefix, 1)
	if message.guild != None:
		if str(message.guild.id) == "787071857794482217":
			if message.content.lower() == "f":
				await message.add_reaction("🇫")
			elif message.content.lower() == "band" and message.author.guild_permissions.manage_messages == True:
				await message.add_reaction("🎺")
				await message.add_reaction("🎸")
				await message.add_reaction("🥁")
				await message.add_reaction("🎷")
				await message.add_reaction("🎤")
	commandList = message.content.split(" ", 1)
	botPing = f"<@!{client.user.id}>"
	if message.content.startswith(botPrefix):
		try:
			message.content = f"{botPrefix}{commandList[0].replace(botPrefix, '').lower()} {commandList[1]}"
		except:
			message.content = f"{botPrefix}{commandList[0].replace(botPrefix, '').lower()}"
	if message.content.startswith(botPing):
		commandList.pop(0)
		try:
			try:
				message.content = f"{botPrefix}{commandList[0].lower()} {commandList[1]}"
			except:
				message.content = f"{botPrefix}{commandList[0].lower()}"
		except:
			pass
	commandName = None
	if botPing in str(message.content):
		try:
			commandName = client.get_command(message.content.replace(botPing, "").split(" ")[1])
		except:
			pass
	if commandName == None:
		commandName = client.get_command(message.content.replace(botPrefix, "").split(" ")[0])
	cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
	Users = cluster["bot"]["Users"]
	memberID = str(message.author.id)
	doc = await Users.find_one({"_id": memberID})
	if doc:
		if not commandName == None:
			if f"{botPrefix}{commandName}" in message.content or f"<@!{client.user.id}> {commandName}" in message.content:
				if "blacklisted" in doc:
					if not doc["blacklisted"] == "no":
						reason = doc["blacklisted"]
						await sendMessage(message.channel, "You are blacklisted!", f"**Reason:**\n{reason}\n\nJoin [here](https://discord.gg/9G9vf6qvdH) and dm Digital_Tech#0001 to appeal a ban.")
						return
	data = await openFile("files/customprefix")
	parent = None
	for botCommand in client.commands:
		if botCommand in (client.commands):
			parent = commandName
			break
		if commandName in botCommand.aliases:
			parent = botCommand
			break
	if not parent == None:
		if not str(parent) in ["botded"]:
			with open("files/stats.json") as jsonFile:
				data = load(jsonFile)
			if str(parent) in data["Commands"]:
				data["Commands"][str(parent)] += 1
			else:
				data["Commands"][str(parent)] = 1
			with open("files/stats.json", "w") as outFile:
				outFile.write(dumps(data, indent = 2))
	if not message.guild == None:
		guildID = str(message.guild.id)	
		with open("files/disabledCommands.json") as jsonFile:
			data = load(jsonFile)
		if guildID in data:
			try:
				if str(commandName) in data[guildID]["commands"]:
					if f"<@!781296717244399617> {commandName}" in str(message.content):
						await sendMessage(message.channel, "This command is disabled!")
						return
					if f"<@!791756099052240936> {commandName}" in str(message.content):
						await sendMessage(message.channel, "This command is disabled!")
						return	 
					if f"{botPrefix}{commandName}" in str(message.content):
						await sendMessage(message.channel, "This command is disabled!")
						return	
			except:
				pass
	cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
	Users = cluster["bot"]["Users"]
	for user in message.mentions:
		memberID = str(user.id)
		doc = await Users.find_one({"_id": memberID})
		if doc:
			if "afk" in doc:
				afkReason = doc["afk"]
				if not "pings" in doc:
					await Users.find_one_and_update({"_id": memberID}, {"$set": {
							"pings": []
							}})
					doc = await Users.find_one({"_id": memberID})
				if not f"{message.author.name} pinged you" in str(doc["pings"]):
					doc = await Users.find_one({"_id": memberID})
					doc["pings"].append(f"{message.author.name} pinged you")
					await Users.find_one_and_update({"_id": memberID}, {"$set": doc})
					doc = await Users.find_one({"_id": memberID})
					if not "afkCount" in doc:
						await Users.find_one_and_update({"_id": memberID}, {"$set": {
							"afkCount": 0
							}})
						doc = await Users.find_one({"_id": memberID})
					if "afkCount" in doc:
						await Users.find_one_and_update({"_id": memberID}, {"$set": {
							"afkCount": doc["afkCount"] + 1
							}})
						doc = await Users.find_one({"_id": memberID})
				embed = discord.Embed(title = f"{user.name} is afk!", description = f"Reason:\n{afkReason}", color = embedColor)
				afkMessage = await message.channel.send(embed = embed)
				await sleep(2.5)
				await afkMessage.delete()
	memberID = str(message.author.id)
	doc = await Users.find_one({"_id": memberID})
	if doc:
		if "afk" in doc:
			doc.pop("afk")
			try:
				Pinglist = "\n".join(doc["pings"])
				pingCount = int(doc["afkCount"])
				doc.pop("afkCount")
				doc.pop("pings")
			except:
				pingCount = 0
				Pinglist = None
			await Users.find_one_and_delete({"_id": memberID})
			await Users.insert_one(doc)
			if Pinglist == None:
				await sendMessage(message.channel, f"{pingCount} user(s) pinged you while you were away!", message = "You are no longer afk!")
			else:
				await sendMessage(message.channel, f"{pingCount} user(s) pinged you while you were away!", Pinglist, message = "You are no longer afk!")
	await client.process_commands(message)

#########################################################################################################################

@client.event
async def on_message_delete(message):
	member = message.author
	avatar = member.avatar_url_as(static_format = "png")
	embed = discord.Embed(color = embedColor, description = f"**Message sent by {member.mention} deleted in {message.channel.mention}**\n{message.content}")
	embed.set_author(name = f"{member}", icon_url = f"{avatar}")
	embed.set_footer(text = f"ID: {member.id} | Message ID: {message.id}")
	await sendLog(message.guild.id, "message", embed)

@client.event
async def on_message_edit(before, after):
	member = before.author
	if member.bot:
		return
	if after.embeds:
		return
	avatar = member.avatar_url_as(static_format = "png")
	embed = discord.Embed(color = embedColor, description = f"**Message sent by {member.mention} edited in {before.channel.mention}**\n\n**Before**:\n{before.content}\n\n**After:**\n{after.content}")
	embed.set_author(name = f"{member}", icon_url = f"{avatar}")
	embed.set_footer(text = f"ID: {member.id} | Message ID: {before.id}")
	await sendLog(before.guild.id, "message", embed)

@client.event
async def on_member_join(member):
	try:
		data = await openFile("files/joinroles")
		guildID = str(member.guild.id)
		if guildID in data:
			for Role in data[guildID]:
				role = discord.utils.get(member.guild.roles, name = Role)
				await member.add_roles(role)
	except:
		pass
	avatar = member.avatar_url_as(static_format = "png")
	embed = discord.Embed(color = embedColor, description = f"**{member.mention} joined.**\n Account created at {str(member.created_at).split(' ')[0]}")
	embed.set_author(name = f"{member}", icon_url = f"{avatar}")
	embed.set_footer(text = f"Member ID: {member.id}")
	await sendLog(member.guild.id, "join/leave", embed)

@client.event
async def on_member_remove(member):
	avatar = member.avatar_url_as(static_format = "png")
	embed = discord.Embed(color = embedColor, description = f"**{member.mention} left.**\n Joined {str(member.joined_at).split(' ')[0]}.")
	embed.set_author(name = f"{member}", icon_url = f"{avatar}")
	embed.set_footer(text = f"Member ID: {member.id}")
	await sendLog(member.guild.id, "join/leave", embed)

@client.event
async def on_guild_join(guild):
	print('+ 1')
	channel = client.get_channel(797897695666372641)
	embed = discord.Embed(title = "New Server!", color = embedColor, description = guild.name)
	embed.add_field(name = "Owner", value = f'{guild.owner}/{guild.owner.id}')
	embed.add_field(name = "Member Count", value = guild.member_count)
	embed.add_field(name = "Booster Level", value = guild.premium_tier)
	embed.add_field(name = "Amount of Boosters", value = guild.premium_subscription_count)
	try:
		await channel.send(embed = embed)
	except:
		pass
	channel = guild.system_channel
	if channel != "None":
		embed = discord.Embed(title = "Thanks for inviting me!", description = "Some things you might want to set up...", color = embedColor)
		embed.add_field(name = "Personalisation", value = "Set up a custom prefix by doing `d!prefix [prefix]`\n do d!mrole to create a muted role!\n If you want to allow gif commands, do d!enablecommand. If you want invalid command errors, just do d!enablecommand invalidCommand!")
		embed.add_field(name = "Logs", value = "Set up audit logs for a multitude of things. Logs keep track of tons of diffrent events that go on in your server, for example, deleted messages. Use `d!setlogs <channel> [category]` to set them up!")
		embed.add_field(name = "Bot changelog", value = "Join my discord server [here](https://discord.gg/9G9vf6qvdH) and follow the changelog in order to get changelogs in your server! If you like using me, use the vote command to vote for me! :)")
		embed.add_field(name = "Support", value = "do d!support to report bugs or something that should not happen. DO NOT USE THIS FOR COMMAND HELP unless the help command doesn't work for you")
		try:
			await channel.send(embed = embed)
		except:
			pass
	disablecommand = client.get_command("disablecommand")
	await disablecommand(guild, "goddamn")
	await disablecommand(guild, "butterdog")
	await disablecommand(guild, "shut")
	await disablecommand(guild, "yikes")
	await disablecommand(guild, "unfunny")
	await disablecommand(guild, "hmm")
	await disablecommand(guild, "google")

@client.event
async def on_guild_remove(guild):
	print('- 1')
	channel = client.get_channel(797897695666372641)
	embed = discord.Embed(title = "Left Server", color = embedColor, description = guild.name)
	embed.add_field(name = "Owner", value = f'{guild.owner}/{guild.owner.id}')
	embed.add_field(name = "Member Count", value = guild.member_count)
	embed.add_field(name = "Booster Level", value = guild.premium_tier)
	embed.add_field(name = "Amount of Boosters", value = guild.premium_subscription_count)
	try:
		await channel.send(embed = embed)
	except:
		pass
	###################################################
	with open("files/auditlog.json") as jsonFile:
		data = load(jsonFile)
	guildID = str(guild.id)
	for category in data:
		if str(guildID) in data[category]:
			data[category].pop(guildID)
	with open("files/auditlog.json", "w") as outFile:
		outFile.write(dumps(data, indent = 2))
	####################################################
	with open("files/customprefix.json") as jsonFile:
		data = load(jsonFile)
	if str(guildID) in data:
		data.pop(guildID)
	with open("files/customprefix.json", "w") as outFile:
		outFile.write(dumps(data, indent = 2))
	####################################################
	with open("files/disabledCommands.json") as jsonFile:
		data = load(jsonFile)
	if str(guildID) in data:
		data.pop(guildID)
	with open("files/disabledCommands.json", "w") as outFile:
		outFile.write(dumps(data, indent = 2))	
	####################################################
	data = await openFile("files/joinroles")
	if str(guildID) in data:
		data.pop(guildID)
	outFile = await writeFile("files/joinroles", data)
	####################################################
	cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
	Guilds = cluster["bot"]["Guilds"]
	await Guilds.find_one_and_delete({"_id": guildID})
	####################################################

@client.event
async def on_guild_channel_update(before, after):
	if not before.name == after.name:
		embed = discord.Embed(color = embedColor, description = f"**Channel Name Edited**\n\n**Before**:\n{before.name}\n\n**After:**\n**{after.name}**")
		embed.set_footer(text = f"Channel ID: {before.id}")
		await sendLog(before.guild.id, "server", embed)
	try:
		if not before.topic == after.topic:
			embed = discord.Embed(color = embedColor, description = f"**Channel Topic Edited**\n\n**Before**:\n{before.topic}\n\n**After:**\n**{after.topic}**")
			embed.set_footer(text = f"Channel ID: {before.id}")
			await sendLog(before.guild.id, "server", embed)
	except:
		return
	if not before.slowmode_delay == after.slowmode_delay:
		embed = discord.Embed(color = embedColor, description = f"**Channel slowmode Edited**\n\n**Before**:\n{before.slowmode_delay}\n\n**After:**\n**{after.slowmode_delay}**")
		embed.set_footer(text = f"Channel ID: {before.id}")
		await sendLog(before.guild.id, "server", embed)		
	if not before.nsfw == after.nsfw:
		embed = discord.Embed(color = embedColor, description = f"**Channel NSFW Edited**\n\n**Before**:\n{before.nsfw}\n\n**After:**\n**{after.nsfw}**")
		embed.set_footer(text = f"Channel ID: {before.id}")
		await sendLog(before.guild.id, "server", embed)
	#if not before.pins == after.pins:
	#	embed = discord.Embed(color = embedColor, description = f"**Channel Pins Edited**\n\n**Before**:\n{before.pins}\n\n**After:**\n**{after.pins}**")
	#	embed.set_footer(text = f"Channel ID: {before.id}")
	#	await sendLog(before.guild.id, "server", embed)

@client.event
async def on_member_update(before, after):
	member = before.name
	if not before.name == after.name:
		embed = discord.Embed(color = embedColor, description = f"**{member}'s name was edited**\n\n**Before**:\n{before.name}\n\n**After:**\n**{after.name}**")
		embed.set_footer(text = f"ID: {before.id}")
		await sendLog(before.guild.id, "member", embed)
	if not before.nick == after.nick:
		embed = discord.Embed(color = embedColor, description = f"**{member}'s nickname was edited**\n\n**Before**:\n{before.nick}\n\n**After:**\n**{after.nick}**")
		embed.set_footer(text = f"ID: {before.id}")
		await sendLog(before.guild.id, "member", embed)	
	#if not before.discriminator == after.discriminator:
	#	embed = discord.Embed(color = embedColor, description = f"**{member}'s discriminator was edited**\n\n**Before**:\n{before.discriminator}\n\n**After:**\n**{after.discriminator}**")
	#	embed.set_footer(text = f"ID: {before.id}")
	#	await sendLog(before.guild.id, "member", embed) #not working
	#if not before.avatar_url_as(static_format = "png") == after.avatar_url_as(static_format = "png"):
	#	embed = discord.Embed(color = embedColor, description = f"**{member}'s avatar was edited**\n\n**Avatar:**")
	#	embed.set_thumbnail(url = after.avatar_url_as(static_format = "png"))
	#	await sendLog(before.guild.id, "member", embed)	# not working				

@client.event
async def on_guild_role_update(before, after):
	role = before.name
	if not before.name == after.name:
		embed = discord.Embed(color = embedColor, description = f"**{role} name was edited**\n\n**Before**:\n{before.name}\n\n**After:**\n**{after.name}**")
		embed.set_footer(text = f"Role ID: {before.id}")
		await sendLog(before.guild.id, "server", embed)
	if not before.colour == after.colour:
		embed = discord.Embed(color = embedColor, description = f"**{role} colour was edited**\n\n**Before**:\n{before.colour}\n\n**After:**\n**{after.colour}**")
		embed.set_footer(text = f"Role ID: {before.id}")
		await sendLog(before.guild.id, "server", embed)		

@client.event
async def on_voice_state_update(member, before, after):
	try:
		vcBefore = before.channel.name
	except:
		vcBefore = "Joined Voice Channel"
	try:
		vcAfter = after.channel.name
	except:
		vcAfter = "Left Voice Channel"
	if not vcBefore == vcAfter:
		embed = discord.Embed(color = embedColor, description = f"**{member} changed voice channel.**\n\n**Before**:\n{vcBefore}\n\n**After:**\n**{vcAfter}**")
		embed.set_footer(text = f"ID: {member.id}")
		try:
			await sendLog(member.guild.id, "voice", embed)	
		except:
			pass
	if before.channel != None:
		oldChannel = client.get_channel(before.channel.id)
		if len(oldChannel.members) == 1:
			if client.user in oldChannel.members:
				vc = member.guild.voice_client
				await vc.disconnect()
				try:
					del client.playedSongs[str(member.guild.id)]
				except:
					pass
				try:
					del client.songQueue[str(member.guild.id)]
				except:
					pass
				try:
					del client.Playloop[guildID]
				except:
					pass

@client.event
async def on_member_ban(guild, user):
	embed = discord.Embed(color = embedColor, description = f"**{user} was banned**\n\n**{user.mention} was banned from {guild}**")
	embed.set_footer(text = f"ID: {user.id}")
	await sendLog(guild.id, "moderation", embed)

#########################################################################################################################

@client.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def embed(ctx, title, *, description = None):
	await ctx.trigger_typing()
	if description == None:
		description = ""
	embed = discord.Embed(title = title, description = description, color = embedColor)
	await ctx.message.reply(embed = embed)

@client.command()
@commands.is_owner()
async def reload(ctx, category):
	await ctx.trigger_typing()
	try:
		client.unload_extension(f"{category}")
		client.load_extension(f"{category}")
		await sendMessage(ctx, f"{category} has been reloaded!")
	except:
		await sendMessage(ctx, "Could not reload that cog.")

@client.event
async def on_raw_reaction_add(payload):
	if payload.member.bot:
		return	
	data = await openFile("files/reactionRoles")
	guild = client.get_guild(payload.guild_id)
	messageID = str(payload.message_id)
	emojiName = str(payload.emoji.name)
	try:
		if messageID in data:
			for reactions in data[messageID]:
				if emojiName in reactions:
					role = get(guild.roles, name = reactions[emojiName])
					await payload.member.add_roles(role)
	except:
		pass

@client.event
async def on_raw_reaction_remove(payload):
	try:
		if payload.member.bot:
			return
	except:
		pass
	data = await openFile("files/reactionRoles")
	guild = client.get_guild(payload.guild_id)
	member = guild.get_member(payload.user_id)
	messageID = str(payload.message_id)
	emojiName = str(payload.emoji.name)
	try:
		if messageID in data:
			for reactions in data[messageID]:
				if emojiName in reactions:
					role = get(guild.roles, name = reactions[emojiName])
					await member.remove_roles(role)
	except:
		pass
	
@client.event
async def on_command_error(ctx, error):
	title = None
	description = None
	if isinstance(error, commands.CommandNotFound):
		return
	elif isinstance(error, commands.MissingPermissions):
		title = "Missing Permissions"
		missingPerms = " ".join(error.missing_perms)
		description = f"You do not have `{missingPerms}`."
	elif isinstance(error, commands.MissingRequiredArgument):
		title = "Missing required parameter"
		description = f"Please enter: `{error.param.name}`"
	elif isinstance(error, commands.MemberNotFound):
		title = "Member not found"
		description = "Please enter in a valid user"
	elif isinstance(error, commands.CommandOnCooldown):
		title = "You are on a cooldown!"
		description = f"Please try again in `{round(error.retry_after)} seconds`"
	elif "Command raised an exception: Forbidden: 403 Forbidden (error code: 50013): Missing Permissions" in str(error):
		title = "I do not have permission to do that!"
		description = "You are trying to have me do something that my role doesn't allow me to do! Either move my role up on the list, above the muted role, or allow my role to allow me to preform this action."
	elif "Command raised an exception: OverflowError: Python int too large to convert to C int" in str(error):
		title = "That number is too big!"
		description = "Please use a smaller number."
	elif isinstance(error, commands.NotOwner):
		title = "Only the owner can use this command!"
		description = "If you think this is a mistake contact the owner using `d!support`!"
	elif "Command raised an exception: ValueError: invalid literal for int() with base 10:" in str(error):
		title = "That is not a number!"
		description = "Please input a valid number!"
	if not title == None:
		await sendMessage(ctx, title, description)	
		return
	try:
		if not "discord.ext.commands.errors.CommandNotFound" in str(error):
			await sendMessage(ctx, "Error:", str(error))
			channel = client.get_channel(797898972144205834)
			await sendMessage(channel, f"{str(error)} happened in `{ctx.guild.id}/{ctx.guild.name}`.", f"{str(error)} in  `{ctx.channel.id}/{ctx.channel.name}` with `{ctx.message.content}`, caused by {ctx.author.id}/{ctx.author.name}#{ctx.author.discriminator}")	
	except:
		if not "discord.ext.commands.errors.CommandNotFound" in str(error):
			print(error)

t = Thread(target=partial_run)
t.start()
client.run(token)