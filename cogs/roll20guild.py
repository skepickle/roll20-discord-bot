from discord.ext import commands
from .utils import db
from .utils.formats import Plural
from collections import defaultdict

import discord
import re

class Roll20Guilds(db.Table, table_name='roll20_guilds'):
    id = db.Column(db.Integer(big=True), primary_key=True) # this is the Discord guild id (snowflake)
    campaign = db.Column(db.Integer(big=True))             # just an internal ID of the campaign in roll20_campaign table

class DisambiguateGuild(commands.Converter):
    async def convert(self, ctx, argument):
        # check if it's a guild ID
        match = ctx.bot.get_guild(argument)

        if match is None:
            raise commands.BadArgument("Could not found this guild.")

        return match

def valid_campaign(argument):
    arg = argument.strip('"')
    return arg

class Roll20Guild(commands.Cog, name='Config'):
    def __init__(self, bot):
        self.bot = bot

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)

    @commands.group(name='guild', invoke_without_command=True)
    async def _guild(self, ctx, *, guild: DisambiguateGuild = None):
        """Manages guilds.

        If you don't pass in a subcommand, it will do a lookup based on
        the guild of the context. If no guild is present in context,
        bot-admins can get a list of guilds.

        All commands will create a guild for bot-admin or guild owner.
        """

        guild = guild or ctx.guild

        query = """SELECT * FROM roll20_guilds WHERE id=$1;"""
        record = await ctx.db.fetchrow(query, guild.id)

        if record is None:
            if guild == ctx.guild:
                await ctx.send('You did not set up this guild.' \
                              f' If you want to input a default campaign ID, type {ctx.prefix}guild campaign 012345' \
                              f' or check {ctx.prefix}help guild')
            else:
                await ctx.send('This guild did not set up.')
            return

        # 0xF02D7D - Splatoon 2 Pink
        # 0x19D719 - Splatoon 2 Green
        e = discord.Embed(colour=0xF02D7D)

        keys = {
            'campaign': 'Campaign'
        }

        for key, value in keys.items():
            e.add_field(name=value, value=record[key] or 'N/A', inline=True)

        await ctx.send(embed=e)

    async def edit_fields(self, ctx, **fields):
        keys = ', '.join(fields)
        values = ', '.join(f'${2 + i}' for i in range(len(fields)))

        query = f"""INSERT INTO roll20_guilds (id, {keys})
                    VALUES ($1, {values})
                    ON CONFLICT (id)
                    DO UPDATE
                    SET ({keys}) = ROW({values});
                 """

        await ctx.db.execute(query, ctx.guild.id, *fields.values())

    @_guild.command(name='campaign')
    async def _campaign(self, ctx, *, campaign: valid_campaign):
        """Sets the Roll20 portion of your player."""
        await self.edit_fields(ctx, campaign=campaign)
        await ctx.send('Updated Campaign.')

    @_guild.command()
    async def delete(self, ctx, *, field=None):
        """Deletes a field from your player.

        The valid fields that could be deleted are:

        - campaign

        Omitting a field will delete your entire player.
        """

        if ctx.guild is None:
            # Then command is being executed in direct-message. Check to see if auther is bot-admin.
            if ctx.bot.is_owner(ctx.author):
                if field is None:
                    await ctx.send('You did not specify the guild id to delete.')
                    return
                guild = DisambiguateGuild(ctx, field)
                confirm = await ctx.prompt("Are you sure you want to delete your guild?")
                if confirm:
                    query = "DELETE FROM roll20_guilds WHERE id=$1;"
                    await ctx.db.execute(query, guild.id)
                    await ctx.send('Successfully deleted guild.')
                else:
                    await ctx.send('Aborting guild deletion.')
            return

        # simple case: delete entire guild
        if field is None:
            confirm = await ctx.prompt("Are you sure you want to delete your guild?")
            if confirm:
                query = "DELETE FROM roll20_guilds WHERE id=$1;"
                await ctx.db.execute(query, ctx.guild.id)
                await ctx.send('Successfully deleted guild.')
            else:
                await ctx.send('Aborting guild deletion.')
            return

        field = field.lower()

        valid_fields = ( 'campaign' )

        if field not in valid_fields:
            return await ctx.send("I don't know what field you want me to delete here bub.")

        # a little intermediate case, basic field deletion:
        field_to_column = {
            'campaign': 'campaign'
        }

        column = field_to_column.get(field)
        if column:
            query = f"UPDATE roll20_guilds SET {column} = NULL WHERE id=$1;"
            await ctx.db.execute(query, ctx.guild.id)
            return await ctx.send(f'Successfully deleted {field} field.')

def setup(bot):
    bot.add_cog(Roll20Guild(bot))
