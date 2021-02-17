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
import ibl
try:
	from Bot import sendMessage
except:
	from Bot1 import sendMessage

class fun(commands.Cog):

	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def goddamn(self, ctx):
		await ctx.trigger_typing()
		try:
			data = await openFile("files/colors")
			if str(ctx.guild.id) in data:
				color = data[str(ctx.guild.id)]["color"]
			else:
				color = ctx.bot.embedColor
		except:
			color = ctx.bot.embedColor
		embed = discord.Embed(title = "Damn... :tired_face:", color = color)
		embed.set_image(url = "https://media.discordapp.net/attachments/736965208076976188/764828263507820544/image0.gif")
		await ctx.message.reply(embed = embed)
	
	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def butterdog(self, ctx):
		await ctx.trigger_typing()
		try:
			data = await openFile("files/colors")
			if str(ctx.guild.id) in data:
				color = data[str(ctx.guild.id)]["color"]
			else:
				color = ctx.bot.embedColor
		except:
			color = ctx.bot.embedColor
		embed = discord.Embed(title = "ButterDog", color = ccolor)
		embed.set_image(url = "https://cdn.discordapp.com/attachments/753738964216709280/787159035866382346/butterdog.gif")
		await ctx.message.reply(embed = embed)
	
	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def shut(self, ctx):
		await ctx.trigger_typing()
		try:
			data = await openFile("files/colors")
			if str(ctx.guild.id) in data:
				color = data[str(ctx.guild.id)]["color"]
			else:
				color = ctx.bot.embedColor
		except:
			color = ctx.bot.embedColor
		embed = discord.Embed(title = "Shut", color = color)
		embed.set_image(url = "https://cdn.discordapp.com/attachments/787182274504294400/787187354430996520/tenor_1.gif")
		await ctx.message.reply(embed = embed)
	
	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def yikes(self, ctx):
		await ctx.trigger_typing()
		await ctx.message.reply("https://cdn.discordapp.com/attachments/716661044289863711/770941943597367296/YIKESHOLYSHIT.mp4")
	
	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def unfunny(self, ctx):
		await ctx.trigger_typing()
		try:
			data = await openFile("files/colors")
			if str(ctx.guild.id) in data:
				color = data[str(ctx.guild.id)]["color"]
			else:
				color = ctx.bot.embedColor
		except:
			color = ctx.bot.embedColor
		embed = discord.Embed(title = "Where is the funny?", color = color)
		embed.set_image(url = "https://cdn.discordapp.com/attachments/791469412002824255/792532800549027841/tenor_2.gif")
		await ctx.message.reply(embed = embed)

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def hmm(self, ctx):
		await ctx.trigger_typing()
		try:
			data = await openFile("files/colors")
			if str(ctx.guild.id) in data:
				color = data[str(ctx.guild.id)]["color"]
			else:
				color = ctx.bot.embedColor
		except:
			color = ctx.bot.embedColor
		embed = discord.Embed(title = "Hmmmmm...", color = color)
		embed.set_image(url = "https://cdn.discordapp.com/attachments/733418529671610493/802668344754700308/unknown.gif")
		await ctx.message.reply(embed = embed)

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def google(self, ctx):
		await ctx.trigger_typing()
		await ctx.message.reply("https://cdn.discordapp.com/attachments/680928395399266314/775723784971354132/c0cec10890e16f6b.mp4")

	@commands.command()
	@commands.has_permissions(manage_messages = True)
	@commands.guild_only()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def bean(self, ctx, member, *, reason = None):
		await ctx.trigger_typing()
		if reason == None:
			reason = "No reason given"
		await sendMessage(ctx, "User has been beaned!", f"{member} was beaned for reason: {reason}")
	
	@commands.command(aliases = ["8ball"])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def eightball(self, ctx, *, message):
		await ctx.trigger_typing()
		reply = [
			"It is certain.",
			"It is decidedly so.",
			"Without a doubt.",
			"Yes – definitely.",
			"As I see it, yes.",
			"Most likely.",
			"Outlook good.",
			"Yes.",
			"Signs point to yes.",
			"Reply hazy, try again.",
			"Ask again later.",
			"Better not tell you now.",
			"Cannot predict now.",
			"Concentrate and ask again.",
			"Don't count on it.",
			"My reply is no.",
			"My sources say no.",
			"Outlook not so good.",
			"Very doubtful."
		]
		await sendMessage(ctx, f"{(random.choice(reply))}")

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def pong(self, ctx):
		await ctx.trigger_typing()
		await sendMessage(ctx, "ping! 🏓")

def setup(bot):
	bot.add_cog(fun(bot))