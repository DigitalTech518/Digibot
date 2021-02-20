from datetime import datetime, timedelta, time
from discord.ext import commands
from json import load, dumps
from asyncio import sleep
from re import search
import discord
from discord.utils import get
from platform import system
import motor.motor_asyncio
try:
	from Bot import sendMessage, sendLog, writeFile, openFile, removeRemind, remindLoopStart, remindLoop
except:
	from Bot1 import sendMessage, sendLog, writeFile, openFile, removeRemind, remindLoopStart, remindLoop

class Utility(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def repeatreminder(self, ctx, time,*, reason = None):
		await ctx.trigger_typing()
		guildID = str(ctx.guild.id)
		memberID = str(ctx.author.id)
		m = search(r"([\d.]+)([smhdwy]?)", time)
		time = float(m.group(1))
		length = m.group(2)
		await sendMessage(ctx, "Repeating Reminder", f"Reminding you every {int(time)}{length} to {reason}", footer = "Use d!reminders to view reminder, and d!removereminder to remove it")
		if length == "":
			length = "m"
		if length == "s":
			finaltime = time
		elif length == "h":
			finaltime = time * 3600
		elif length == "d":
			finaltime = time * 86400
		elif length == "w":
			finaltime = time * 604800
		elif length == "y":
			finaltime = time * 31536000
		else:
			finaltime = time * 60
		cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
		Users = cluster["bot"]["Users"]
		doc = await Users.find_one({"_id": memberID})
		if not doc:
			await Users.insert_one({
				"_id": memberID,
				"reminders": []
				})
		await Users.find_one_and_update({"_id": memberID},{
			"$addToSet":{
				"reminders":{
					"time": str(datetime.now()  + timedelta(seconds = finaltime)).split(".")[0],
					"channelID": ctx.channel.id,
					"reason": reason,
					"finaltime": finaltime
			}}})	
		updated = await Users.find_one({"_id": memberID})
		await remindLoopStart()

	@commands.command()
	@commands.has_permissions(manage_guild = True)
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def customcolor(self, ctx, color):
		await ctx.trigger_typing()
		match = search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', color)
		if match:
			try:
				newColorr = color.split("#")[1]
			except:
				pass
			newColor = int(newColorr, 16)
			guildID = str(ctx.guild.id)
			data = await openFile("files/colors")
			if not guildID in data:
				data[guildID] = {}
			data[guildID]["color"] = newColorr
		else:
			await sendMessage(ctx, "That isn't a valid hex color!")
			return
		outFile = await writeFile("files/colors", data)
		await sendMessage(ctx, f"{newColorr} has been set as the embed color!")

	@commands.command()
	@commands.has_permissions(manage_guild = True)
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def removecolor(self, ctx):
		await ctx.trigger_typing()
		guildID = str(ctx.guild.id)
		data = await openFile("files/colors")
		if guildID in data:
			del data[guildID]
		else:
			await sendMessage(ctx, "You don't have a color set!")
		outFile = await writeFile("files/colors", data)
		await sendMessage(ctx, f"Color has been reset!")

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def viewcolor(self, ctx):
		await ctx.trigger_typing()
		guildID = str(ctx.guild.id)
		data = await openFile("files/colors")
		if guildID in data:
			await sendMessage(ctx, f"The current set color is #{data[guildID]['color']}")
		else:
			await sendMessage(ctx, "You don't have a color set!")

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def afk(self, ctx, *, reason = None):
		await ctx.trigger_typing()
		if reason == None:
			reason = "None"
		memberID = str(ctx.author.id)
		cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
		Users = cluster["bot"]["Users"]
		doc = await Users.find_one({"_id": memberID})
		if not doc:
			Users.insert_one({
				"_id": memberID,
				"afk": reason
				})
			doc = await Users.find_one({"_id": memberID})
			await sendMessage(ctx, "You have been set to AFK")
			return
		if not "afk" in doc:
			await Users.find_one_and_update({"_id": memberID}, {"$set": {
				"afk" : reason
				}})
			doc = await Users.find_one({"_id": memberID})
			await sendMessage(ctx, "You have been set to AFK")
			return
		if "afk" in doc:
			doc.pop("afk")
			await Users.find_one_and_delete({"_id": memberID})
			await Users.insert_one(doc)
			await sendMessage(ctx, "You have been set to not AFK!")
			return


	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def removenote(self, ctx, name, entry = None):
		if not entry == None:
			try:
				int(entry)
			except:
				await sendMessage(ctx, "Entry must be a number above 0!")
				return
		memberID = str(ctx.author.id)
		cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
		Users = cluster["bot"]["Users"]
		doc = await Users.find_one({"_id": memberID})
		if not doc:
			await sendMessage(ctx, "You do not have any notes!")
			return
		if not "notes" in doc:
			await sendMessage(ctx, "You do not have any notes!")
			return
		List = []
		x = -1
		a = False
		for Name in doc["notes"]:
			x = x + 1
			for NAME in doc["notes"][x]:
				nname = str(NAME).split("'")[1]
				List.append(str(nname))
				if str(name) in List:
					if a != True:
						y = x
						Nname = nname
					a = True
		if a == False:
			await sendMessage(ctx, "You do not have a note by that name!")
			return
		if not entry == None:
			try:
				try:
					doc["notes"][y][0][name].pop(int(entry) - 1)
					if len(doc["notes"][y][0][name]) < 1:
						doc["notes"][y][0].pop(name)
						doc["notes"].pop(y)
				except:
					doc["notes"][y -1][0][name].pop(int(entry - 1))
					if len(doc["notes"][y -1][0][name]) < 1:
						doc["notes"][y -1][0].pop(name)
						doc["notes"].pop(y - 1)
			except:
				await sendMessage(ctx, f"You do not have a entry at `{entry}` in note `{name}`")
				return
			await Users.find_one_and_update({"_id": memberID}, {"$set": doc})
		else:
			try:
				doc["notes"][y][0].pop(name)
				doc["notes"].pop(y)
			except:
				doc["notes"][y -1][0].pop(name)
				doc["notes"].pop(y - 1)
			await Users.find_one_and_update({"_id": memberID}, {"$set": doc})
		if not entry == None:
			await sendMessage(ctx, f"{entry} has been removed from {name}")
		else:
			await sendMessage(ctx, f"{name} has been deleted")

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def notes(self, ctx, name = None):
		memberID = str(ctx.author.id)
		cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
		Users = cluster["bot"]["Users"]
		doc = await Users.find_one({"_id": memberID})
		if not doc:
			await sendMessage(ctx, "You do not have any notes!")
			return
		if not "notes" in doc:
			await sendMessage(ctx, "You do not have any notes!")
			return
		if len(doc["notes"]) < 1:
			await sendMessage(ctx, "You do not have any notes!")
			return
		List = []
		x = -1
		a = False
		for Name in doc["notes"]:
			x = x + 1
			for NAME in doc["notes"][x]:
				nname = str(NAME).split("'")[1]
				List.append(str(nname))
				if str(name) in List:
					if a != True:
						y = x
						Nname = nname
					a = True
		if name == None:
			Message = "\n".join(List)
			await sendMessage(ctx, "Note names:", Message)
			return
		if a == False:
			await sendMessage(ctx, "You do not have a note by that name!")
			return
		try:
			Message = "\n".join(doc["notes"][y][0][name])
		except:
			Message = "\n".join(doc["notes"][y -1][0][name])
		await sendMessage(ctx, f"Content of {name}", Message)

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def notepad(self, ctx, name, *, entry):
		memberID = str(ctx.author.id)
		cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
		Users = cluster["bot"]["Users"]
		doc = await Users.find_one({"_id": memberID})
		if not doc:
			await Users.insert_one({
				"_id": memberID,
				"notes": []
				})
			doc = await Users.find_one({"_id": memberID})
		if not "notes" in doc:
			await Users.find_one_and_update({"_id": memberID}, {"$set": {
				"notes": []
				}})
			doc = await Users.find_one({"_id": memberID})
		List = []
		x = -1
		a = False
		for Name in doc["notes"]:
			x = x + 1
			for NAME in doc["notes"][x]:
				nname = str(NAME).split("'")[1]
				List.append(str(nname))
				if str(name) in List:
					if a != True:
						y = x
						Nname = nname
					a = True
		if a == False:
			await Users.find_one_and_update({"_id": memberID}, {"$addToSet": {
					"notes": [{
						name: []
					}
					]	
					}})
		doc = await Users.find_one({"_id": memberID})
		try:
			 doc["notes"][y][0][name].append(entry)
		except:
			doc["notes"][x + 1][0][name].append(entry)
		await Users.find_one_and_update({"_id": memberID}, {"$set": doc})
		await sendMessage(ctx, "Note has been added to notepad!", f"`{name}` has been updated with entry `{entry}`")


	@commands.command(aliases = ["delete", "begone"])
	@commands.has_permissions(manage_messages = True)
	@commands.guild_only()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def purge(self, ctx, amount):
		await ctx.trigger_typing()
		try:
			await ctx.channel.purge(limit = int(amount)+1)
			try:
				data = await openFile("files/colors")
				if str(ctx.guild.id) in data:
					color = data[str(ctx.guild.id)]["color"]
				else:
					color = ctx.bot.embedColor
			except:
				color = ctx.bot.embedColor
			embed = discord.Embed(title = f"Purged {amount} messages from chat", color = color)
			message = await ctx.send(embed = embed)
			await sleep(1)
			await message.delete()
		except:
			pass

	@commands.command(aliases = ["reminder", "remind"])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def remindme(self, ctx, time,*, reason = None):
		await ctx.trigger_typing()
		guildID = str(ctx.guild.id)
		memberID = str(ctx.author.id)
		m = search(r"([\d.]+)([smhdwy]?)", time)
		time = float(m.group(1))
		length = m.group(2)
		await sendMessage(ctx, "Reminder", f"Reminding you in {int(time)}{length} to {reason}.")
		if length == "":
			length = "m"
		if length == "s":
			finaltime = time
		elif length == "h":
			finaltime = time * 3600
		elif length == "d":
			finaltime = time * 86400
		elif length == "w":
			finaltime = time * 604800
		elif length == "y":
			finaltime = time * 31536000
		else:
			finaltime = time * 60
		cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
		Users = cluster["bot"]["Users"]
		doc = await Users.find_one({"_id": memberID})
		if not doc:
			await Users.insert_one({
				"_id": memberID,
				"reminders": []
				})
		await Users.find_one_and_update({"_id": memberID},{
			"$addToSet":{
				"reminders":{
					"time": str(datetime.now()  + timedelta(seconds = finaltime)).split(".")[0],
					"channelID": ctx.channel.id,
					"reason": reason
			}}})	
		updated = await Users.find_one({"_id": memberID})
		await remindLoopStart()

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def reminders(self, ctx):
		await ctx.trigger_typing()
		memberID = str(ctx.author.id)
		cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
		Users = cluster["bot"]["Users"]
		doc = await Users.find_one({"_id": memberID})
		reminders = []
		for item in doc["reminders"]:
			if not len(item) < 1:
				reminders.append(f'**Reminder:** {item["reason"]}')
				reminders.append(f'**Time of reminder:** {item["time"]}')
				if "finaltime" in item:
					reminders.append(f"**Repeating:** Yes")
				reminders.append("- - - - - - - - - - - - - - - - - - - -")
		if len(reminders) < 1:
			await sendMessage(ctx, "*Error.* This user most likely has no reminders")
			return
		reminders = "\n".join(reminders)
		await sendMessage(ctx, f"{ctx.author.name}'s Reminders!", f"{reminders}")
	
	@commands.command(aliases = ["Rreminder"])
	@commands.guild_only()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def removereminder(self, ctx, reminder):
		await ctx.trigger_typing()
		memberID = str(ctx.author.id)
		cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
		Users = cluster["bot"]["Users"]
		doc = await Users.find_one({"_id": memberID})
		reminderNum = int(reminder) - 1
		if reminderNum < 0:
			await sendMessage(ctx, "Enter in a valid number")
		else:
			try:
				doc["reminders"].remove(doc["reminders"][reminderNum])
				await Users.find_one_and_update({"_id": memberID}, {"$set": doc})
				await sendMessage(ctx, f"Reminder number {reminder} was removed for {ctx.author.name}.")
			except:
				await sendMessage(ctx, "You do not have any reminders")

	@commands.command(aliases = ["temp"])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def temperature(self, ctx, temperature, tempType, convType):
		await ctx.trigger_typing()
		tempType = tempType.lower()
		convType = convType.lower()
		if tempType == "f" and convType == "c":
			newTemp = (int(temperature) -32) * 5/9
			await sendMessage(ctx, f"{round(int(newTemp))} in C.")
		elif tempType == "c" and convType == "c":
			await sendMessage(ctx, f"{temperature} in C.")
		elif tempType == "k" and convType == "c":
			newTemp = int(temperature) - 273.15
			await sendMessage(ctx, f"{round(int(newTemp))} in C.")
		elif tempType == "f" and convType == "f":
			await sendMessage(ctx, f"{temperature} in F.")
		elif tempType == "c" and convType == "f":
			newTemp = (int(temperature) * 9/5) + 32
			await sendMessage(ctx, f"{round(int(newTemp))} in F.")
		elif tempType == "k" and convType == "f":
			newTemp = (int(temperature) - 273.15) * 9/5 + 32
			await sendMessage(ctx, f"{round(int(newTemp))} in F.")
		elif tempType == "f" and convType == "k":
			newTemp = (int(temperature) - 32) * 5/9 + 273.15
			await sendMessage(ctx, f"{round(int(newTemp))} in K.")
		elif tempType == "c" and convType == "k":
			newTemp = int(temperature) + 273.15
			await sendMessage(ctx, f"{round(int(newTemp))} in K.")
		elif tempType == "k" and convType == "k":
			await sendMessage(ctx, f"{temperature} in K.")
		else:
			await sendMessage(ctx, "That is not a valid temperature!")

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def settime(self, ctx, offset):
		await ctx.trigger_typing()
		if offset == None:
			await sendMessage(ctx, "Enter in an UTC offset!")
			return
		data = await openFile("files/times")
		data[str(ctx.author.id)] = (int(offset))
		outFile = await writeFile("files/times", data)
		await sendMessage(ctx, f"UTC offset has been set to {offset}")

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def time(self, ctx, member: discord.Member = None):
		await ctx.trigger_typing()
		data = await openFile("files/times")
		if member == None:
			member = ctx.author
		if str(member.id) in data:
			offset = data[str(member.id)]
		else:
			await sendMessage(ctx, "You do not have a set time!")
			return
		if system() == "Windows":
			timeDif = timedelta(hours = int(offset) + 6)
		if not system() == "Windows":
			timeDif = timedelta(hours = int(offset))
		await sendMessage(ctx, f"Date and time for {member.name}", f"**Date:** {str(datetime.now() + timeDif).split(' ')[0]}\n**Time:** {str(datetime.now() + timeDif).split(' ')[1].split('.')[0]}")

	@commands.command()
	@commands.has_permissions(manage_roles = True)
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def addreactionrole(self, ctx, message: discord.Message, emoji, role: discord.Role):
		await ctx.trigger_typing()
		messageID = str(message.id)
		try:
			emojiN = str(emoji).split(":")[1]
		except:
			emojiN = emoji
		data = await openFile("files/reactionRoles")
		if not messageID in data:
			data[messageID] = []
		if len(data[messageID]) > 0:
			data[messageID].append({
				emojiN : role.name
				})
		if len(data[messageID]) == 0:
			data[messageID].append({
				emojiN : role.name
				})
		await message.add_reaction(emoji)
		outFile = await writeFile("files/reactionRoles", data)
		await sendMessage(ctx, "Reaction Roles added!")
	
	@commands.command()
	@commands.has_permissions(manage_roles = True)
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def removereactionrole(self, ctx, message: discord.Message):
		await ctx.trigger_typing()
		data = await openFile("files/reactionRoles")
		if not str(message.id) in data:
			await sendMessage(ctx, "That message has no reaction roles!")
			return
		data.pop(str(message.id))
		outFile = await writeFile("files/reactionRoles", data)
		await sendMessage(ctx, "Reaction roles has been removed!")

def setup(bot):
	bot.add_cog(Utility(bot))