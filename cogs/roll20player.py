from discord.ext import commands
from .utils import db
from .utils.formats import Plural
from collections import defaultdict

import discord
import re

class Roll20PlayersTable(db.Table, table_name='roll20_players'):
  # The Discord member id (snowflake)
  id = db.Column(db.Integer(big=True), primary_key=True)
  # The Roll20 user id (integer)
  roll20 = db.Column(db.Integer(big=True))

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
        raise commands.BadArgument(
          f'Could not find this member. {e}') from None

    if result is None:
      raise commands.BadArgument(
        "Could not find this member. Note this is case sensitive.")
    return result

def valid_roll20(argument):
  arg = argument.strip('"')
  try:
    val = int(str(arg))
  except ValueError:
    raise commands.BadArgument('A Roll20 user id must be an integer: {}'.format(argument))
  return val

class Roll20Player(commands.Cog, name='Config'):
  def __init__(self, bot):
    self.bot = bot

  async def cog_command_error(self, ctx, error):
    if isinstance(error, commands.BadArgument):
      await ctx.send(error)

  @commands.group(name='player')
  async def _player(self, ctx):
    """Handles players' information.

    This is information about IRL players."""

    if ctx.invoked_subcommand is None:
      await ctx.send_help('player')

  @_player.command(name="list")
  async def _player_list(self, ctx):
    """Administrator command to list players."""
    if (not await ctx.bot.is_owner(ctx.author)):
      await ctx.send('You do not have permission to run this command.')
      return
    if ctx.guild is not None:
      await ctx.send('This command must be run from DM.')
      return

    query = """SELECT * FROM roll20_players;"""
    records = await ctx.db.fetch(query)
    print(records)
    return

  @_player.command(name='get')
  async def _player_get(self, ctx, *, member: DisambiguateMember = None):
    """Display player information.

    This shows information to the player.

    If executed by guild owner, a member
    may be passed in as an argument."""

    if member is not None:
      if ctx.guild is None:
        if (not await ctx.bot.is_owner(ctx.author)):
          await ctx.send('You do not have permission to specify members on this command in DMs')
          return
        else:
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
        await ctx.send('You did not set up a player record.' \
                      f' If you want to create a record, type {ctx.prefix}player set' \
                      f' or check {ctx.prefix}help player set')
      else:
        await ctx.send('This member did not create a player record.')
      return

    e = None

    if (record['roll20']):
      e = discord.Embed(description = "Roll20 User ID is set.",
                        color=0xF02D7D)
      e.set_author(name=member.display_name,
                   url='https://app.roll20.net/users/{}'.format(record['roll20']),
                   icon_url=member.avatar_url_as(format='png'))
    else:
      e = discord.Embed(title = member.display_name,
                        description = "Roll20 User ID is not set.",
                        color=0xF02D7D)
      e.set_author(name=member.display_name,
                   icon_url=member.avatar_url_as(format='png'))

    await ctx.send(embed=e)

  #async def edit_fields(self, ctx, member: DisambiguateMember, **fields):
  #  keys = ', '.join(fields)
  #  values = ', '.join(f'${2 + i}' for i in range(len(fields)))

  #  query = f"""INSERT INTO roll20_players (id, {keys})
  #              VALUES ($1, {values})
  #              ON CONFLICT (id)
  #              DO UPDATE
  #              SET ({keys}) = ROW({values});
  #           """

  #  await ctx.db.execute(query, member.id, *fields.values())

  #@_player.group(name='set')
  #async def _set(self, ctx):
  #  """Sets a player's field value."""

  #  if ctx.invoked_subcommand is None:
  #    await ctx.send_help('set')

  @_player.command(name='set')
  async def _set(self, ctx, field, value, *, member: DisambiguateMember = None):
    """Sets a player's field value.

    The valid fields that can be set are:
    - roll20"""

    if member is not None:
      if (not await ctx.bot.is_owner(ctx.author)):
        await ctx.send('You do not have permission to specify members on this command')
        return

    member = member or ctx.author

    if field is None:
      return await ctx.send("A field must be specified.")

    if value is None:
      return await ctx.send("A value must be specified.")

    field = field.lower()
    value = value.strip('"')

    valid_fields = ( 'roll20' )

    if field not in valid_fields:
      return await ctx.send("I don't know what field you want me to set.")

    field_to_column = {
      'roll20': 'roll20'
    }

    column = field_to_column.get(field)
    if column:
      if column == 'roll20':
        val = value
        try:
          value = int(str(value))
        except ValueError:
          raise commands.BadArgument('A Roll20 user id must be an integer: {}'.format(val))

      query = f"""INSERT INTO roll20_players (id, {column})
                VALUES ($1, {value})
                ON CONFLICT (id)
                DO UPDATE
                SET ({column}) = ROW({value});
             """
      await ctx.db.execute(query, member.id)
      return await ctx.send(f'Successfully set {field} field to "{value}".')

  @_player.command(name='unset')
  async def _unset(self, ctx, field, *, member: DisambiguateMember = None):
    """Unsets a player's field value.

    The valid fields that could be unset are:
    - roll20"""

    if member is not None:
      if (not await ctx.bot.is_owner(ctx.author)):
        await ctx.send('You do not have permission to specify members on this command')
        return

    member = member or ctx.author

    if field is None:
      return await ctx.send("A field must be specified.")

    field = field.lower()

    valid_fields = ( 'roll20' )

    if field not in valid_fields:
      return await ctx.send("I don't know what field you want me to unset.")

    field_to_column = {
      'roll20': 'roll20'
    }

    column = field_to_column.get(field)
    if column:
      query = f"UPDATE roll20_players SET {column} = NULL WHERE id=$1;"
      await ctx.db.execute(query, member.id)
      return await ctx.send(f'Successfully unset {field} field.')

  @_player.command(name='delete')
  async def _delete(self, ctx, *, member: DisambiguateMember = None):
    """Delete your entire player record."""
    if (not await ctx.bot.is_owner(ctx.author)):
      if member is not None:
        await ctx.send('You do not have permission to specify members on this command')
        return

    prompt_str = "Are you sure you want to delete this player record?"
    if member is None:
      prompt_str = "Are you sure you want to delete your player record?"
            
    member = member or ctx.author

    #TODO Check that 'member' is not referenced to from other tables.

    confirm = await ctx.prompt(prompt_str)
    if confirm:
      query = "DELETE FROM roll20_players WHERE id=$1;"
      await ctx.db.execute(query, ctx.author.id)
      await ctx.send('Successfully deleted player.')
    else:
      await ctx.send('Aborting player deletion.')
    return

def setup(bot):
  bot.add_cog(Roll20Player(bot))
