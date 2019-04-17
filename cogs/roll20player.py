from discord.ext import commands
from .utils import db
from .utils.formats import Plural
from collections import defaultdict

import discord
import re

class Roll20PlayersTable(db.Table, table_name='roll20_players'):
    id = db.Column(db.Integer(big=True), primary_key=True) # this is the Discord member id (snowflake)
    roll20 = db.Column(db.Integer(big=True))               # this is the Roll20 user id (integer)

class DisambiguateMember(commands.IDConverter):
    async def convert(self, ctx, argument):
        # check if it's a user ID or mention
        match = self._get_id_match(argument) or re.match(r'<@!?([0-9]+)>$', argument)

        if match is not None:
            # exact matches, like user ID + mention should search
            # for every member we can see rather than just this guild.
            user_id = int(match.group(1))
            result = ctx.bot.get_user(user_id)
            if result is None:
                raise commands.BadArgument("Could not find this member.")
            return result

        # check if we have a discriminator:
        if len(argument) > 5 and argument[-5] == '#':
            # note: the above is true for name#discrim as well
            name, _, discriminator = argument.rpartition('#')
            pred = lambda u: u.name == name and u.discriminator == discriminator
            result = discord.utils.find(pred, ctx.bot.users)
        else:
            # disambiguate I guess
            if ctx.guild is None:
                matches = [
                    user for user in ctx.bot.users
                    if user.name == argument
                ]
                entry = str
            else:
                matches = [
                    member for member in ctx.guild.members
                    if member.name == argument
                    or (member.nick and member.nick == argument)
                ]

                def to_str(m):
                    if m.nick:
                        return f'{m} (a.k.a {m.nick})'
                    else:
                        return str(m)

                entry = to_str

            try:
                result = await ctx.disambiguate(matches, entry)
            except Exception as e:
                raise commands.BadArgument(f'Could not find this member. {e}') from None

        if result is None:
            raise commands.BadArgument("Could not found this member. Note this is case sensitive.")
        return result

def valid_roll20(argument):
    arg = argument.strip('"')
    try:
       val = int(str(arg))
    except ValueError:
        raise commands.BadArgument('An Roll20 user id must be an integer.')
    return val

class Roll20Player(commands.Cog, name='Config'):
    def __init__(self, bot):
        self.bot = bot

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)

    @commands.group(name='player')
    async def _player(self, ctx):
        """Handles the player configuration."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help('player')

    @_player.command(name='get')
    async def _get(self, ctx, *, member: DisambiguateMember = None):
        """Display player configuration."""
        if ctx.guild is None:
            if member is not None:
                if (not ctx.bot.is_owner(ctx.author)):
                    await ctx.send('You do not have permission to specify members on this command in DMs')
                    return
        else:
            if member is not None:
                if (ctx.author is not ctx.guild.owner):
                    await ctx.send('You do not have permission to specify members on this command')
                    return
                if (member not in ctx.guild.members):
                    await ctx.send('The player specified is not a member of this guild')
                    return
            
        member = member or ctx.author

        query = """SELECT * FROM roll20_players WHERE id=$1;"""
        record = await ctx.db.fetchrow(query, member.id)

        if record is None:
            if member == ctx.author:
                await ctx.send('You did not set up a player.' \
                              f' If you want to input a Roll20 user ID, type {ctx.prefix}player roll20 012345' \
                              f' or check {ctx.prefix}help player')
            else:
                await ctx.send('This member did not set up a player.')
            return

        # 0xF02D7D - Splatoon 2 Pink
        # 0x19D719 - Splatoon 2 Green
        e = discord.Embed(colour=0xF02D7D)

        #keys = {
        #    'roll20': 'Roll20 User ID'
        #}

        #for key, value in keys.items():
        #    e.add_field(name=value, value=record[key] or 'N/A', inline=True)

        # consoles = [f'__{v}__: {record[k]}' for k, v in keys.items() if record[k] is not None]
        # e.add_field(name='Consoles', value='\n'.join(consoles) if consoles else 'None!', inline=False)

        if (record['roll20']):
            //e.add_field(name='Roll20 User ID', value='Set', inline=False)
            e.set_author(name=member.display_name, url='https://app.roll20.net/users/{}'.format(record['roll20']), icon_url=member.avatar_url_as(format='png'))
        else:
            e.add_field(name='Roll20 User ID', value='Unset', inline=False)
            e.set_author(name=member.display_name, icon_url=member.avatar_url_as(format='png'))

        await ctx.send(embed=e)

    async def edit_fields(self, ctx, **fields):
        keys = ', '.join(fields)
        values = ', '.join(f'${2 + i}' for i in range(len(fields)))

        query = f"""INSERT INTO roll20_players (id, {keys})
                    VALUES ($1, {values})
                    ON CONFLICT (id)
                    DO UPDATE
                    SET ({keys}) = ROW({values});
                 """

        await ctx.db.execute(query, ctx.author.id, *fields.values())

    @_player.group(name='set')
    async def _set(self, ctx):
        """Set options of player."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(_player)

    @_set.command(name='roll20')
    async def _set_roll20(self, ctx, *, ROLL20: valid_roll20):
        """Sets the Roll20 portion of your player."""
        await self.edit_fields(ctx, roll20=ROLL20)
        await ctx.send('Updated Roll20.')

    @_player.command(name='delete')
    async def _delete(self, ctx, *, field=None):
        """Deletes a field from your player.

        The valid fields that could be deleted are:

        - roll20

        Omitting a field will delete your entire player.
        """

        # simple case: delete entire player
        if field is None:
            confirm = await ctx.prompt("Are you sure you want to delete your player?")
            if confirm:
                query = "DELETE FROM roll20_players WHERE id=$1;"
                await ctx.db.execute(query, ctx.author.id)
                await ctx.send('Successfully deleted player.')
            else:
                await ctx.send('Aborting player deletion.')
            return

        field = field.lower()

        valid_fields = ( 'roll20' )

        if field not in valid_fields:
            return await ctx.send("I don't know what field you want me to delete here bub.")

        # a little intermediate case, basic field deletion:
        field_to_column = {
            'roll20': 'roll20'
        }

        column = field_to_column.get(field)
        if column:
            query = f"UPDATE roll20_players SET {column} = NULL WHERE id=$1;"
            await ctx.db.execute(query, ctx.author.id)
            return await ctx.send(f'Successfully deleted {field} field.')

def setup(bot):
    bot.add_cog(Roll20Player(bot))
