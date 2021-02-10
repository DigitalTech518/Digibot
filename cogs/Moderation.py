from datetime import datetime, timedelta, time
from discord.ext import commands
from json import load, dumps
from asyncio import sleep
import requests
import discord
from discord.utils import get
from re import search
import motor.motor_asyncio
try:
	from Bot import sendMessage, sendLog, writeFile, openFile, removeMutes, muteLoopStart, muteLoop
except:
	from Bot1 import sendMessage, sendLog, writeFile, openFile, removeMutes, muteLoopStart, muteLoop

class Moderation(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	@commands.has_permissions(kick_members = True)
	@commands.guild_only()
	async def kick(self, ctx, member:discord.Member, *, reason = 'No reason given'):
		await ctx.trigger_typing()
		await member.kick(reason = reason)        
		await sendMessage(ctx, "Member was kicked", f"{member.mention} was kicked from the server. ({reason})", None, f"Moderator Responsible: {ctx.author.id}")
		try:
			await sendMessage(await getLog(ctx.guild.id, "moderation"), "Member was kicked", f"{member.mention} was kicked from the server. ({reason})", None, f"Moderator Responsible: {ctx.author.id}")
		except:
			pass

	@commands.command()
	@commands.has_permissions(ban_members = True)
	@commands.guild_only()
	async def ban(self, ctx, member:discord.Member, *, reason = 'No reason given'):
		await ctx.trigger_typing()
		await member.ban(reason = reason)        
		await sendMessage(ctx, "Member was banned", f"{member.mention} was banned from the server. ({reason})")

	@commands.command()
	@commands.has_permissions(manage_messages = True)
	@commands.guild_only()
	async def permamute(self, ctx, member: discord.Member, *, reason = "no reason"):
		await ctx.trigger_typing()
		data = await openFile("files/mutes")
		guildID = str(ctx.guild.id)
		memberID = str(member.id)
		if not guildID in data:
			data[guildID] = {}
		if not memberID in data[guildID]:
			data[guildID][memberID] = []
		data[guildID][memberID].append({
			"name": str(member),
			"reason": reason,
			"date": str(ctx.message.created_at).split('.')[0]
			})
		role = discord.utils.get(member.guild.roles, name='Muted')
		await member.add_roles(role)
		await sendMessage(ctx, "Member was muted.", f"{member.mention} was muted. ({reason})")
		try:
			await sendMessage(await getLog(ctx.guild.id, "moderation"), "Member was permamuted", f"{member.mention} was permamuted. ({reason})", None, f"Moderator Responsible: {ctx.author.id}")
		except:
			pass
		outFile = await writeFile("files/mutes", data)

	@commands.command()
	@commands.has_permissions(manage_messages = True)
	@commands.guild_only()
	async def unmute(self, ctx, member: discord.Member, *, reason = "no reason"):
		await ctx.trigger_typing()
		role = discord.utils.get(member.guild.roles, name='Muted')
		if role not in member.roles:
			await sendMessage(ctx, "Failed to unmute", f"{member.name} is not muted")
			return
		guildID = str(ctx.guild.id)
		memberID = str(member.id)
		cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
		Guilds = cluster["bot"]["Guilds"]
		doc = await Guilds.find_one({"_id": guildID})
		if "Mutes" in doc:
			if memberID in doc["Mutes"]["activeMutes"]:
				doc["Mutes"]["activeMutes"].pop(memberID, None)
				await Guilds.find_one_and_update({"_id": guildID}, {"$set": doc})
		await member.remove_roles(role)
		await sendMessage(ctx, "Member was unmuted.", f"{member.mention} was unmuted. ({reason})")
		try:
			await sendMessage(await getLog(ctx.guild.id, "moderation"), "Member was unmuted", f"{member.mention} was unmuted. ({reason})", None, f"Moderator Responsible: {ctx.author.id}")
		except:
			pass

	@commands.command()
	@commands.has_permissions(manage_messages = True)
	@commands.guild_only()
	async def mute(self, ctx, member: discord.Member, mute_time = "5", *, reason = "no reason"):
		await ctx.trigger_typing()
		m = search(r"([\d.]+)([smhdw]?)", mute_time)
		try:
			time = float(m.group(1))
			length = m.group(2)
		except:
			if reason == "no reason":
				reason = mute_time
			else:
				reason = f"{mute_time} {reason}"
			time = 5
			length = "m"
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
		else:
			finaltime = time * 60
		timeA = f"{time}{length}"
		role = discord.utils.get(ctx.guild.roles, name="Muted")
		guildID = str(ctx.guild.id)
		memberID = str(member.id)
		cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
		Guilds = cluster["bot"]["Guilds"]
		doc = await Guilds.find_one({"_id": guildID})
		if not doc:
			await Guilds.insert_one({"_id": guildID})
			doc = await Guilds.find_one({"_id": guildID})
		if not "Mutes" in doc:
			await Guilds.find_one_and_update({"_id": guildID}, {"$set": {
				"Mutes": {}
				}})
			doc = await Guilds.find_one({"_id": guildID})
		if not memberID in doc["Mutes"]:
			await Guilds.find_one_and_update({"_id": guildID}, {"$set": {
				"Mutes": {
					memberID : []
				}
				}})
			doc = await Guilds.find_one({"_id": guildID})
		if not "activeMutes" in doc["Mutes"]:
			doc["Mutes"]["activeMutes"] = {
						memberID: {
							"time": str(datetime.now()  + timedelta(seconds = finaltime)).split(".")[0],
							"channelID": ctx.channel.id
				}}
			await Guilds.find_one_and_update({"_id": guildID}, {"$set": doc})
			doc = await Guilds.find_one({"_id": guildID})
		if "activeMutes" in doc["Mutes"]:
			doc["Mutes"]["activeMutes"] = {
						memberID: {
							"time": str(datetime.now()  + timedelta(seconds = finaltime)).split(".")[0],
							"channelID": ctx.channel.id
				}}
			await Guilds.find_one_and_update({"_id": guildID}, {"$set": doc})
			doc = await Guilds.find_one({"_id": guildID})	
		doc["Mutes"][memberID].append({
			"moderator responsible": str(ctx.author.id),
			"reason": reason,
			"date": str(ctx.message.created_at).split('.')[0],
			"length": timeA
			})
		await Guilds.find_one_and_update({"_id": guildID}, {"$set": doc})
		await member.add_roles(role)
		await sendMessage(ctx, "Member was muted.", f"{member.mention} was muted for {int(time)}{length}. ({reason})")
		try:
			await sendMessage(await getLog(ctx.guild.id, "moderation"), "Member was muted", f"{member.mention} was muted. ({reason})", None, f"Moderator Responsible: {ctx.author.id}")
		except:
			pass
		await muteLoopStart()

	@commands.command()
	@commands.has_permissions(manage_messages = True)
	@commands.guild_only()
	async def warn(self, ctx, member: discord.Member = None, *, reason = "No Reason."):
		await ctx.trigger_typing()
		if member == None:
			await sendMessage(ctx, "You can't warn yourself", "Please select a member to warn")
			return	
		guildID = str(ctx.guild.id)
		memberID = str(member.id)
		moderator = str(ctx.author.id)
		cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
		Guilds = cluster["bot"]["Guilds"]
		doc = await Guilds.find_one({"_id": guildID})
		if member.roles[-1].position > ctx.author.roles[-1].position:
			await sendMessage(ctx, "You cannot warn someone above your own role!")
			return
		if not doc:
			await Guilds.insert_one({"_id": guildID})
			doc = await Guilds.find_one({"_id": guildID})
		if not "Warns" in doc:
			await Guilds.find_one_and_update({"_id": guildID}, {"$set": {
				"Warns" : {}
				}})
			doc = await Guilds.find_one({"_id": guildID})
		if not memberID in doc["Warns"]:
			await Guilds.find_one_and_update({"_id": guildID}, {"$set": {
				"Warns" : {
				memberID: []
				}}})
			doc = await Guilds.find_one({"_id": guildID})
		doc["Warns"][memberID].append({
			"reason": reason,
			"date": str(ctx.message.created_at).split('.')[0],
			"moderator": moderator
		})
		await Guilds.find_one_and_update({"_id": guildID}, {"$set": doc})
		doc = await Guilds.find_one({"_id": guildID})
		embed = discord.Embed(title = f"{member.name} has been warned", color = ctx.bot.embedColor)
		embed.add_field(name = "Reason:", value = reason, inline = False)
		embed.add_field(name = "# of Warns", value = len(doc["Warns"][memberID]), inline = False)
		embed.set_footer(text = f"Moderator Responsible: {moderator}")
		await ctx.message.reply(embed = embed)
		try:
			await member.send(embed=embed)
		except:
			pass
		await sendLog(ctx.guild.id, "moderation", embed)

	@commands.command()
	@commands.has_permissions(ban_members = True)
	@commands.guild_only()
	async def pardonwarn(self, ctx, member: discord.Member, number):
		await ctx.trigger_typing()
		data = await openFile("files/warns")
		guildID = str(ctx.guild.id)
		memberID = str(member.id)
		cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
		Guilds = cluster["bot"]["Guilds"]
		doc = await Guilds.find_one({"_id": guildID})
		warning = int(number) - 1
		if warning < 0:
			await sendMessage(ctx, "Enter in a valid number")
		else:
			doc["Warns"][memberID].pop(warning)
			await Guilds.find_one_and_update({"_id": guildID}, {"$set": doc})
			await sendMessage(ctx, f"Warning number {number} was removed for {member.name}.")

	@commands.command()
	@commands.guild_only()
	@commands.has_permissions(administrator = True)
	async def unban(self, ctx, ID, *, reason):
		await ctx.trigger_typing()
		try:
			ID = int(ID)
		except:
			await sendMessage("Invalid ID")
		banlist = await  ctx.guild.bans()
		x = 0
		for entry in banlist:
			if ID == entry.user.id:
				break
			x += 1
		else:
			await sendMessage(ctx, "User ID not found", "Enter a banned user ID")
			return
		await ctx.guild.unban(banlist[x].user)
		await sendMessage(ctx,"User has been unbanned")
		embed = discord.Embed(color = ctx.bot.embedColor, title = "User was unbanned", description = f"**<@{ID}> was unbanned**")
		embed.add_field(name = "Reason", value=reason, inline = False)
		embed.set_footer(text = f"ID: {ID}")
		try:
			await sendMessage(await getLog(ctx.guild.id, "moderation"), "Member was unbanned", f"<@{ID}> was unbanned.", None, f"Moderator Responsible: {ctx.author.id}")
		except:
			pass

	@commands.command(aliases = ["mrole"])
	@commands.has_permissions(manage_roles = True)
	@commands.guild_only()
	async def mutedrole(self, ctx):
		await ctx.trigger_typing()
		roles = ""
		for i in ctx.guild.roles:
			roles += i.name + " "
		if "Muted" in roles:
			await sendMessage(ctx, "You all ready have a muted role!")
			return
		elif "Muted" not in roles:
			role = await ctx.guild.create_role(name = "Muted", permissions = discord.Permissions(send_messages = False), color = discord.Color(ctx.bot.mutedColor))
			channels = ctx.guild.text_channels
			for channels in channels:
				await channels.set_permissions(role, send_messages=False, add_reactions = False)
			for x in reversed(range(len(ctx.guild.roles))):
				try:
					await role.edit(position = x)
					break
				except:
					pass
			await sendMessage(ctx, "Muted Role Created!")

	@commands.command()
	@commands.guild_only()
	@commands.has_permissions(manage_messages = True)
	async def modnote(self, ctx, user: discord.User, *, note):
		await ctx.trigger_typing()
		guildID = str(ctx.guild.id)
		memberID = str(user.id)
		cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
		Guilds = cluster["bot"]["Guilds"]
		doc = await Guilds.find_one({"_id": guildID})
		if not doc:
			await Guilds.insert_one({"_id": guildID})
			doc = await Guilds.find_one({"_id": guildID})
		if not "Notes" in doc:
			await Guilds.find_one_and_update({"_id": guildID}, {"$set": {
				"Notes" : {}
				}})
			doc = await Guilds.find_one({"_id": guildID})
		if not memberID in doc["Notes"]:
			await Guilds.find_one_and_update({"_id": guildID}, {"$set": {
				"Notes": {
				memberID : []
				}
				}})
			doc = await Guilds.find_one({"_id": guildID})
		doc["Notes"][memberID].append({
			"Responsible Moderator:": str(ctx.author.id),
			"Date:": str(ctx.message.created_at).split(".")[0],
			"Note:": note
			})
		await Guilds.find_one_and_update({"_id": guildID}, {"$set": doc})
		await sendMessage(ctx, f"Note created for {user.name}.", f"**Note:**\n{note}")

	@commands.command()
	@commands.guild_only()
	@commands.has_permissions(manage_messages = True)
	async def pardonnote(self, ctx, user: discord.User, noteNum):
		await ctx.trigger_typing()
		noteNum = int(noteNum) - 1
		guildID = str(ctx.guild.id)
		memberID = str(user.id)
		cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
		Guilds = cluster["bot"]["Guilds"]
		doc = await Guilds.find_one({"_id": guildID})
		if not "Notes" in doc:
			await sendMessage(ctx, f"{user.name} has no notes set!")
			return
		if not memberID in doc["Notes"]:
			await sendMessage(ctx, f"{user.name} has no notes set!")
			return
		else:
			doc["Notes"][memberID].pop(noteNum)
			await Guilds.find_one_and_update({"_id": guildID}, {"$set": doc})
			await sendMessage(ctx, f"Modnote {int(noteNum) + 1} has been removed.")

	@commands.command()
	@commands.guild_only()
	@commands.has_permissions(manage_messages = True)
	async def records(self, ctx, user: discord.User):
		await ctx.trigger_typing()
		guildID = str(ctx.guild.id)
		memberID = str(user.id)
		cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
		Guilds = cluster["bot"]["Guilds"]
		####################################################
		doc = await Guilds.find_one({"_id": guildID})
		Notes = []
		if "Notes" in doc:
			if memberID in doc["Notes"]:
				for note in doc["Notes"][memberID]:
					Notes.append(f'**Responsible Moderator:** {note["Responsible Moderator:"]}')
					Notes.append(f'**Date of note:** {note["Date:"]}')
					Notes.append(f'**Note:** {note["Note:"]}')
					Notes.append("- - - - - - - - - - - - - - - - - - - -")
		if len(Notes) >= 1:
			NoteList = "\n".join(Notes) 
		else:
			NoteList = "None"
		####################################################
		doc = await Guilds.find_one({"_id": guildID})
		Mutes = []
		if "Mutes" in doc:
			if memberID in doc["Mutes"]:
				for mute in doc["Mutes"][memberID]:
					Mutes.append(f'**Moderator Responsible:** {mute["moderator responsible"]}')
					Mutes.append(f'**Reason:** {mute["reason"]}')
					Mutes.append(f'**Date:** {mute["date"]}')
					Mutes.append(f'**Length:** {mute["length"]}')
					Mutes.append("- - - - - - - - - - - - - - - - - - - -")
		if len(Mutes) >= 1:
			muteList = "\n".join(Mutes)
		else:
			muteList = "None"
		####################################################
		doc = await Guilds.find_one({"_id": guildID})
		Warns = []
		if "Warns" in doc:
			if memberID in doc["Warns"]:
				for warn in data["Warns"][memberID]:
					Warns.append(f'**Reason:** {warn["reason"]}')
					Warns.append(f'**Date:** {warn["date"]}')
					Warns.append(f'**Moderator Responsible:** {warn["moderator"]}')
					Warns.append("- - - - - - - - - - - - - - - - - - - -")
		if len(Warns) >= 1:
			warnList = "\n".join(Warns)
		else:
			warnList = "None"
		####################################################
		await sendMessage(ctx,f"Records for {user.name}", f"***Notes:***\n{str(NoteList)}\n***Mutes:***\n{str(muteList)}\n***Warns:***\n{str(warnList)}")

def setup(bot):
	bot.add_cog(Moderation(bot))