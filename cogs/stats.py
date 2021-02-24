from discord.ext import commands

import statcord


class StatcordPost(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api = statcord.Client(self.bot, self.bot.statKey)
        self.api.start_loop()


    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.api.command_run(ctx)


def setup(bot):
    bot.add_cog(StatcordPost(bot))