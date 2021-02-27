from datetime import datetime, timedelta, time
from discord.ext import commands, tasks
from asyncio import sleep
import requests
import discord
import aiohttp
import asyncpg
from json import loads
from platform import system 

class StatsUpload(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.VoidUpload.start()
		self.VoidUpload.add_exception_type(asyncpg.PostgresConnectionError)
		self.SpaceUpload.start()
		self.SpaceUpload.add_exception_type(asyncpg.PostgresConnectionError)

	@tasks.loop(minutes = 30)
	async def VoidUpload(self):
		await self.bot.wait_until_ready()
		async with aiohttp.ClientSession() as session:
			async with session.post(url = f"https://api.voidbots.net/bot/stats/{self.bot.user.id}", headers = {"content-type":"application/json", "Authorization": self.bot.voidToken}, json = {"server_count": len(self.bot.guilds)}) as r:
				pass

	@tasks.loop(minutes = 30)
	async def SpaceUpload(self):
		await self.bot.wait_until_ready()
		async with aiohttp.ClientSession() as session:
			async with session.post(url = f"https://api.botlist.space/v1/bots/{self.bot.user.id}", headers = {"content-type":"application/json", "Authorization": self.bot.spaceToken}, json = {"server_count": len(self.bot.guilds)}) as r:
				pass

def setup(bot):
	bot.add_cog(StatsUpload(bot))