from datetime import datetime, timedelta, time
from discord.ext import commands, tasks
from json import load, dumps
from asyncio import sleep, run_coroutine_threadsafe, get_event_loop
import requests
import discord
from discord.utils import get
from fast_youtube_search import search_youtube
from youtube_dl import YoutubeDL
import math
try:
	from Bot import sendMessage, sendLog, writeFile, openFile
except:
	from Bot1 import sendMessage, sendLog, writeFile, openFile

def playNext(ctx):
	guildID = str(ctx.guild.id )
	if not guildID in ctx.bot.songQueue:
		return
	if len(ctx.bot.songQueue[guildID]) == 1:
		del ctx.bot.songQueue[guildID]
	elif len(ctx.bot.songQueue[guildID]) > 1:
		del ctx.bot.songQueue[guildID][0]
		info = ctx.bot.songQueue[guildID][0]
		beforeArgs = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
		embed = discord.Embed(title = f"Now playing `{info['title']}`", color = ctx.bot.embedColor)
		embed.set_thumbnail(url = f"https://img.youtube.com/vi/{info['id']}/maxresdefault.jpg")
		embed.set_author(name = "Click here to open online", url = f"https://youtu.be/{info['id']}")
		run_coroutine_threadsafe(ctx.send(embed = embed), ctx.bot.eventLoop)
		ctx.guild.voice_client.play(discord.FFmpegPCMAudio(info["url"], before_options = beforeArgs,  options = "-loglevel panic"), after = lambda e: playNext(ctx))

class Music(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def play(self, ctx, *, song):
		await ctx.trigger_typing()
		if ctx.message.author.voice == None:
			await sendMessage(ctx, "You aren't in a voice channel!")
			return
		try:
			results = search_youtube([song])
		except:
			await ctx.message.add_reaction("❌")
			return
		try:
			url = f"https://youtu.be/{results[0]['id']}"
		except:
			await sendMessage(ctx, f"No songs where found under the name `{song}`")
			return
		ydl_opts = {
			"format": "bestaudio",
			"quiet": True
		}
		with YoutubeDL(ydl_opts) as ydl:
			try:
				info = ydl.extract_info(url, download = False)
			except:
				await sendMessage(ctx, "Video is unsupported!")
				return
		channel = ctx.message.author.voice.channel
		try:
			vc = await channel.connect()
			await ctx.guild.change_voice_state(channel = channel, self_deaf = True)
		except:
			vc = ctx.guild.voice_client
			await ctx.guild.change_voice_state(channel = channel, self_deaf = True)
		if not channel == ctx.guild.get_member(self.bot.user.id).voice.channel:
			await sendMessage(ctx, "Unavaliable", "I am already in another voice channel!")
			return
		songJson = {
			"id": info["id"],
			"title": info["title"],
			"url": info["formats"][0]["url"],
			"duration": info["duration"]
		}
		if not str(ctx.guild.id) in ctx.bot.songQueue:
			ctx.bot.songQueue[str(ctx.guild.id)] = []
		if not str(ctx.guild.id) in ctx.bot.playedSongs:
			ctx.bot.playedSongs[str(ctx.guild.id)] = []
		ctx.bot.songQueue[str(ctx.guild.id)].append(songJson)
		ctx.bot.playedSongs[str(ctx.guild.id)].append(songJson)
		if not vc.is_playing():
			beforeArgs = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
			embed = discord.Embed(title = f"Now playing `{info['title']}`", color = ctx.bot.embedColor)
			embed.set_thumbnail(url = f"https://img.youtube.com/vi/{info['id']}/maxresdefault.jpg")
			embed.set_author(name = "Click here to open online", url = url)
			await ctx.message.reply(mention_author = False, embed = embed)
			try:
				vc.play(discord.FFmpegPCMAudio(info["formats"][0]["url"], before_options = beforeArgs,  options = "-loglevel panic"), after = lambda e: playNext(ctx))
			except:
				pass
		else:
			embed = discord.Embed(title = f"Queued `{info['title']}`", color = ctx.bot.embedColor)
			embed.set_thumbnail(url = f"https://img.youtube.com/vi/{info['id']}/maxresdefault.jpg")
			embed.set_author(name = "Click here to open online", url = url)
			await ctx.message.reply(mention_author = False, embed = embed)	

	@commands.command(aliases = ["fuckoff"])
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def leave(self, ctx):
		global voteCount
		vc = ctx.guild.voice_client
		moderator = False
		if ctx.author.guild_permissions.manage_messages == True:
			moderator = True
		if ctx.message.author.voice == None:
			await sendMessage(ctx, "You are not in a voice channel!")
			return
		voice_channel = discord.utils.get(ctx.message.guild.channels, id = vc.channel.id)
		if vc:
			members = []
			for member in voice_channel.members:
				if not member.bot:
					members.append(member.id)
			if len(members) > 1 and moderator == False:
				await ctx.trigger_typing()
				voteCount = 0
				y = len(members)
				vote = y//2
				if len(members) == 2:
					vote = 2
				embed = discord.Embed(title = f"Needs {vote} votes to leave!", color = ctx.bot.embedColor)
				voteMessage = await ctx.send(embed = embed)
				await voteMessage.add_reaction("⬆️")
				def check(reaction, user):
					global voteCount
					if user.id in members and reaction.message.id == voteMessage.id and str(reaction) == "⬆️":
						voteCount += 1
						return voteCount == vote
				try:
					await self.bot.wait_for("reaction_add", check = check, timeout = 60)
				except:
					await sendMessage(ctx, "Vote has timed out")
					return
				await vc.disconnect()
				await ctx.message.add_reaction("👋")
				await voteMessage.delete()
			else:
				try:
					await vc.disconnect()
					await ctx.message.add_reaction("👋")
				except:
					await sendMessage(ctx, "Cannot leave voice channel.")

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def skip(self, ctx):
		vc = ctx.guild.voice_client
		if ctx.message.author.voice == None:
			await sendMessage(ctx, "You are not in a voice channel!")
			return
		global voteCount
		moderator = False
		if ctx.author.guild_permissions.manage_messages == True:
			moderator = True
		voice_channel = discord.utils.get(ctx.message.guild.channels, id = vc.channel.id)
		if vc:
			if not str(ctx.guild.id) in ctx.bot.songQueue:
				await sendMessage(ctx, "Cannot skip this song, you have no songs in the queue")
				return
			members = []
			for member in voice_channel.members:
				if not member.bot:
					members.append(member.id)
			if len(members) > 1 and moderator == False:
				await ctx.trigger_typing()
				voteCount = 0
				y = len(members)
				vote = y//2
				if len(members) == 2:
					vote = 2
				embed = discord.Embed(title = f"Needs {vote} votes to skip!", color = ctx.bot.embedColor)
				voteMessage = await ctx.send(embed = embed)
				await voteMessage.add_reaction("⬆️")
				def check(reaction, user):
					global voteCount
					if user.id in members and reaction.message.id == voteMessage.id and str(reaction) == "⬆️":
						voteCount += 1
						return voteCount == vote
				try:
					await self.bot.wait_for("reaction_add", check = check, timeout = 60)
				except:
					await sendMessage(ctx, "Vote has timed out")
					return
				vc.stop()
				await ctx.message.add_reaction("⏩")
				await voteMessage.delete()
			else:
				try:
					vc.stop()
					await ctx.message.add_reaction("⏩")
				except:
					await sendMessage(ctx, "Cannot skip music")

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def stop(self, ctx):
		vc = ctx.guild.voice_client
		if ctx.message.author.voice == None:
			await sendMessage(ctx, "You are not in a voice channel!")
			return
		global voteCount
		moderator = False
		if ctx.author.guild_permissions.manage_messages == True:
			moderator = True
		voice_channel = discord.utils.get(ctx.message.guild.channels, id = vc.channel.id)
		if vc:
			members = []
			for member in voice_channel.members:
				if not member.bot:
					members.append(member.id)
			if len(members) > 1 and moderator == False:
				await ctx.trigger_typing()
				voteCount = 0
				y = len(members)
				vote = y//2
				if len(members) == 2:
					vote = 2
				embed = discord.Embed(title = f"Needs {vote} votes to stop!", color = ctx.bot.embedColor)
				voteMessage = await ctx.send(embed = embed)
				await voteMessage.add_reaction("⬆️")
				def check(reaction, user):
					global voteCount
					if user.id in members and reaction.message.id == voteMessage.id and str(reaction) == "⬆️":
						voteCount += 1
						return voteCount == vote
				try:
					await self.bot.wait_for("reaction_add", check = check, timeout = 60)
				except:
					await sendMessage(ctx, "Vote has timed out")
					return
				ctx.bot.songQueue[str(ctx.guild.id)] = []
				vc.stop()
				await ctx.message.add_reaction("🛑")
				await voteMessage.delete()
			else:
				try:
					ctx.bot.songQueue[str(ctx.guild.id)] = []
					vc.stop()
					await ctx.message.add_reaction("🛑")
				except:
					await sendMessage(ctx, "Cannot stop music")

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def pause(self, ctx):
		vc = ctx.guild.voice_client
		if ctx.message.author.voice == None:
			await sendMessage(ctx, "You are not in a voice channel!")
			return
		global voteCount
		moderator = False
		if ctx.author.guild_permissions.manage_messages == True:
			moderator = True
		voice_channel = discord.utils.get(ctx.message.guild.channels, id = vc.channel.id)
		if vc:
			members = []
			for member in voice_channel.members:
				if not member.bot:
					members.append(member.id)
			if len(members) > 1 and moderator == False:
				await ctx.trigger_typing()
				voteCount = 0
				y = len(members)
				vote = y//2
				if len(members) == 2:
					vote = 2
				embed = discord.Embed(title = f"Needs {vote} votes to pause!", color = ctx.bot.embedColor)
				voteMessage = await ctx.send(embed = embed)
				await voteMessage.add_reaction("⬆️")
				def check(reaction, user):
					global voteCount
					if user.id in members and reaction.message.id == voteMessage.id and str(reaction) == "⬆️":
						voteCount += 1
						return voteCount == vote
				try:
					await self.bot.wait_for("reaction_add", check = check, timeout = 60)
				except:
					await sendMessage(ctx, "Vote has timed out")
					return
				vc.pause()
				await ctx.message.add_reaction("⏸️")
				await voteMessage.delete()
			else:
				try:
					vc.pause()
					await ctx.message.add_reaction("⏸️")
				except:
					await sendMessage(ctx, "Cannot pause music")

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def resume(self, ctx):
		vc = ctx.guild.voice_client
		if ctx.message.author.voice == None:
			await sendMessage(ctx, "You are not in a voice channel!")
			return
		global voteCount
		moderator = False
		if ctx.author.guild_permissions.manage_messages == True:
			moderator = True
		voice_channel = discord.utils.get(ctx.message.guild.channels, id = vc.channel.id)
		if vc:
			members = []
			for member in voice_channel.members:
				if not member.bot:
					members.append(member.id)
			if len(members) > 1 and moderator == False:
				await ctx.trigger_typing()
				voteCount = 0
				y = len(members)
				vote = y//2
				if len(members) == 2:
					vote = 2
				embed = discord.Embed(title = f"Needs {vote} votes to resume!", color = ctx.bot.embedColor)
				voteMessage = await ctx.send(embed = embed)
				await voteMessage.add_reaction("⬆️")
				def check(reaction, user):
					global voteCount
					if user.id in members and reaction.message.id == voteMessage.id and str(reaction) == "⬆️":
						voteCount += 1
						return voteCount == vote
				try:
					await self.bot.wait_for("reaction_add", check = check, timeout = 60)
				except:
					await sendMessage(ctx, "Vote has timed out")
					return
				vc.resume()
				await ctx.message.add_reaction("⏯️")
				await voteMessage.delete()
			else:
				try:
					vc.resume()
					await ctx.message.add_reaction("⏯️")
				except:
					await sendMessage(ctx, "Cannot pause music")

	@commands.command()
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def queue(self, ctx):
		await ctx.trigger_typing()
		guildID = str(ctx.guild.id)
		test = []
		x = 0
		if len(ctx.bot.songQueue) <= 0:
			await sendMessage(ctx, "There is nothing in your queue!")
			return
		for song in ctx.bot.songQueue[guildID]:
			x = x + 1
			seconds = song['duration']%60
			if len(str(seconds)) == 1:
				seconds = f"0{seconds}"
			time = f"{song['duration']//60}:{seconds}"
			if len(song['title']) > 25:
				Test = str(song['title'])[0:25]
				test.append(f"**{x}:** {Test}...   ~   {time}")
			else:
				test.append(f"**{x}** {song['title']}   ~   {time}")
		testList = "\n".join(test)
		if len(testList) <= 0:
			await sendMessage(ctx, "There is nothing in your queue!")
			return
		await sendMessage(ctx, "Queue", str(testList))

	@commands.command()
	@commands.has_permissions(manage_messages = True)
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def clearqueue(self, ctx):
		await ctx.trigger_typing()
		guildID = str(ctx.guild.id)
		songQueue = ctx.bot.songQueue
		vc = ctx.guild.voice_client
		if vc:
			if ctx.message.author.voice == None:
				await sendMessage(ctx, "You are not in a voice channel!")
				return
			if not guildID in songQueue:
				await sendMessage(ctx, "There isn't a queue!")
				return
			del songQueue[guildID]
			await sendMessage(ctx, "Queue has been cleared")

	@commands.command()
	@commands.has_permissions(manage_messages = True)
	@commands.cooldown(1, 5, commands.BucketType.user)
	async def forceskip(self, ctx):
		vc = ctx.guild.voice_client
		if vc:
			if ctx.message.author.voice == None:
				await ctx.trigger_typing()
				await sendMessage(ctx, "You are not in a voice channel!")
				return
			if not str(ctx.guild.id) in ctx.bot.songQueue:
				await ctx.trigger_typing()
				await sendMessage(ctx, "Cannot skip this song, you have no songs in the queue")
				return
			vc.stop()
			await ctx.message.add_reaction("⏩")
			return
		await ctx.trigger_typing()
		await sendMessage(ctx, "Cannot skip music", "No music is playing.")

def setup(bot):
	bot.add_cog(Music(bot))