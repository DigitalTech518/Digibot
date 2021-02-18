from discord.ext import commands
import requests
import discord
from asyncio import sleep
from discord.utils import get
import typing
import motor.motor_asyncio
from re import search
from datetime import datetime, timedelta, time
try:
	from Bot import sendMessage, sendLog, writeFile, openFile, sendDM
except:
	from Bot1 import sendMessage, sendLog, writeFile, openFile, sendDM, removeRemind, remindLoopStart, remindLoop

class Restricted(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(aliases = ["bl?"])
	@commands.is_owner()
	async def isblacklisted(self, ctx, user: discord.User):
		await ctx.trigger_typing()
		userID = str(user.id)
		cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
		Users = cluster["bot"]["Users"]
		doc = await Users.find_one({"_id": userID})
		if not doc:
			await sendMessage(ctx, f"{user.name} is not blacklisted!")
			return
		if not "blacklisted" in doc:
			await sendMessage(ctx, f"{user.name} is not blacklisted!")
			return
		if "blacklisted" in doc:
			if doc["blacklisted"] == "no":
				await sendMessage(ctx, f"{user.name} is not blacklisted!")
				return
			else:
				reason = doc["blacklisted"]
				await sendMessage(ctx, f"{user.name} is blacklisted", f"Reason: `{reason}`")

	@commands.command(aliases = ["bl"])
	@commands.is_owner()
	async def blacklist(self, ctx, user: discord.User, reason = None):
		await ctx.trigger_typing()
		if reason == None:
			reason = "No reason provided"
		userID = str(user.id)
		cluster = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017)
		Users = cluster["bot"]["Users"]
		doc = await Users.find_one({"_id": userID})
		if not doc:
			await Users.insert_one({
				"_id": str(userID),
				"blacklisted": "no"
				})
			doc = await Users.find_one({"_id": userID})
		if not "blacklisted" in doc:
			await Users.find_one_and_update({"_id": userID}, {"$set":{
				"blacklisted": reason
				}})
			await sendMessage(ctx, f"{user.name} has been blacklisted")
		if "blacklisted" in doc:
			if str(doc["blacklisted"]) == "no":
				doc["blacklisted"] = reason
				await sendMessage(ctx, f"{user.name} has been blacklisted")
				await Users.find_one_and_update({"_id": userID}, {"$set": doc})
				return
			else:
				doc["blacklisted"] = "no"
				await sendMessage(ctx, f"{user.name} has been removed from blacklist.")
				await Users.find_one_and_update({"_id": userID}, {"$set": doc})
				return

	@commands.command()
	@commands.is_owner()
	async def botded(self, ctx):
		await ctx.trigger_typing()
		print('Digibot stopped')
		await sendMessage(ctx, "DA BOT HAS DIED")
		await self.bot.close()
	
	@commands.command()
	@commands.is_owner()
	async def dm(self, ctx, user: discord.User, *, message):
		await ctx.trigger_typing()
		await sendDM(user, "Message has been sent by Digi", f"**Message:** {message}", footer = "Use d!support to respond back!")
		await sendMessage(ctx, f"Dm has been sent to {user.name}.", f"Message: {message}")
	
	@commands.command()
	@commands.is_owner()
	async def say(self, ctx, channel: typing.Optional[int] = None, *,message):
		await ctx.trigger_typing()
		if channel == None:
			test = ctx.channel
		if not channel == None:
			test = self.bot.get_channel(int(channel))
		if message == None:
			await sendMessage(ctx, "Enter in a message to say!")
			return
		try:
			await test.send(message)
			await sendMessage(ctx, "Message has been sent!")
		except:
			await sendMessage(ctx, "Message failed to send")

def setup(bot):
	bot.add_cog(Restricted(bot))