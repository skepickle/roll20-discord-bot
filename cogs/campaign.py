from discord.ext import commands
from .utils import db
from .utils.formats import Plural
from collections import defaultdict

import discord
import re

class Campaigns(db.Table, table_name='roll20_campaigns'):
    id = db.Column(db.Integer(big=True), primary_key=True) # just an internal ID

    title = db.Column(db.String) # Title of the Campaign

    gm = db.Column(db.Integer(big=True)) # this is a Discord member id (snowflake)

    url = db.Column(db.String) # URL to bridge handout
    key = db.Column(db.String) # Encryption key for handout

class DisambiguateTitle(commands.Converter):
    async def convert(self, ctx, argument):
        query = """SELECT * FROM roll20_campaigns WHERE id=$1;"""
        record = await ctx.db.fetchrow(query, argument)

        if record is None:
            query = """SELECT * FROM roll20_campaigns WHERE title=$1;"""
            record = await ctx.db.fetchrow(query, argument)

        if record is None:
            raise commands.BadArgument(f'Could not find this campaign.') from None

        return record[id]

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

def valid_title(argument):
    arg = argument.strip('"')
    return arg

def valid_url(argument):
    arg = argument.strip('"')
    #TODO: Make sure argument is a URL
    return arg

def valid_key(argument):
    arg = argument.strip('"')
    return arg

class Campaign(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)

    @commands.group(invoke_without_command=True)
    async def campaign(self, ctx, *, campaign_id: DisambiguateTitle = None):
        """Manages a campaign.

        If you don't pass in a subcommand, it will do a lookup based on
        the title passed in. If no title is passed in, you will
        get the campaign for the current guild or channel.

        All commands will create a campaign if you are the guild owner.
        """

        if campaign_id is None:
            #TODO: Look for close title matches? Or other campaigns already in this guild?
            await ctx.send('You did not specify a campaign')
            return

        query = """SELECT * FROM roll20_campaigns WHERE id=$1;"""
        record = await ctx.db.fetchrow(query, campaign_id)

        #if record is None:
            #if member == ctx.author:
            #    await ctx.send('You did not set up a profile.' \
            #                  f' If you want to input a switch friend code, type {ctx.prefix}profile switch 1234-5678-9012' \
            #                  f' or check {ctx.prefix}help profile')
            #else:
            #    await ctx.send('This member did not set up a profile.')
            #return

        # 0xF02D7D - Splatoon 2 Pink
        # 0x19D719 - Splatoon 2 Green
        e = discord.Embed(colour=0xF02D7D)

        keys = {
            'title': 'Title',
            'url': 'Bridge Handout URL'
        }

        for key, value in keys.items():
            e.add_field(name=value, value=record[key] or 'N/A', inline=True)

        url_key_value = "UNSET"
        if record['key']:
            url_key_value = "*******"
        e.add_field(name='Bridge Handout Key', value=url_key_value, inline=True)

        if record['gm']:
            gm_user = ctx.bot.get_user_info(campaign_id)
            e.set_author(name=gm_user.display_name, icon_url=gm_user.avatar_url_as(format='png'))

        await ctx.send(embed=e)

    async def edit_fields(self, ctx, **fields):
        keys = ', '.join(fields)
        values = ', '.join(f'${2 + i}' for i in range(len(fields)))

        query = f"""INSERT INTO campaigns (id, {keys})
                    VALUES ($1, {values})
                    ON CONFLICT (id)
                    DO UPDATE
                    SET ({keys}) = ROW({values});
                 """

        await ctx.db.execute(query, ctx.author.id, *fields.values())

    @campaign.command()
    async def title(self, ctx, *, TITLE: valid_title):
        """Sets the title of a campaign."""
        await self.edit_fields(ctx, title=TITLE)
        await ctx.send('Updated campaign title.')

    @campaign.command()
    async def gm(self, ctx, *, GM: DisambiguateMember):
        """Sets the GM of a campaign."""
        await self.edit_fields(ctx, gm=GM)
        await ctx.send('Updated campaign gm.')

    @campaign.command()
    async def url(self, ctx, *, URL: valid_url):
        """Sets the URL of the campaign's bridge handout in Roll20."""
        await self.edit_fields(ctx, url=URL)
        await ctx.send('Updated campaign bridge URL.')

    @campaign.command()
    async def key(self, ctx, *, KEY: valid_key):
        """Sets the decryption key of the campaign's bridge handout in Roll20."""
        await self.edit_fields(ctx, key=KEY)
        await ctx.send('Updated campaign bridge key.')

    #@campaign.command()
    #async def switch(self, ctx, *, fc: valid_fc):
    #    """Sets the Switch friend code of your profile."""
    #    await self.edit_fields(ctx, fc_switch=fc)
    #    await ctx.send('Updated Switch friend code.')

    #@campaign.command()
    #async def weapon(self, ctx, *, weapon: SplatoonWeapon):
    #    """Sets the Splatoon 2 weapon part of your profile.

    #    If you don't have a profile set up then it'll create one for you.
    #    The weapon must be a valid weapon that is in the Splatoon database.
    #    If too many matches are found you'll be asked which weapon you meant.
    #    """

    #    query = """INSERT INTO roll20_campaigns (id, extra)
    #               VALUES ($1, jsonb_build_object('sp2_weapon', $2::jsonb))
    #               ON CONFLICT (id) DO UPDATE
    #               SET extra = jsonb_set(profiles.extra, '{sp2_weapon}', $2::jsonb)
    #            """

    #    await ctx.db.execute(query, ctx.author.id, weapon)
    #    await ctx.send(f'Successfully set weapon to {weapon["name"]}.')

    #@campaign.command(usage='<mode> <rank>')
    #async def rank(self, ctx, *, argument: valid_rank):
    #    """Sets the Splatoon 2 rank part of your profile.

    #    You set the rank on a per mode basis, such as

    #    - tc/tower control
    #    - rm/rainmaker
    #    - sz/splat zones/zones
    #    - cb/clam/blitz/clam blitz
    #    """

    #    query = """INSERT INTO roll20_campaigns (id, extra)
    #               VALUES ($1, $2::jsonb)
    #               ON CONFLICT (id) DO UPDATE
    #               SET extra =
    #                   CASE
    #                       WHEN profiles.extra ? 'sp2_rank'
    #                       THEN jsonb_set(profiles.extra, '{sp2_rank}', profiles.extra->'sp2_rank' || $2::jsonb)
    #                       ELSE jsonb_set(profiles.extra, '{sp2_rank}', $2::jsonb)
    #                   END
    #            """

    #    mode, data = argument
    #    await ctx.db.execute(query, ctx.author.id, {mode: data})
    #    await ctx.send(f'Successfully set {mode} rank to {data["rank"]}{data["number"]}.')

    @campaign.command()
    async def delete(self, ctx, *, field=None):
        """Deletes a field from the campaign.

        The valid fields that could be deleted are:

        - gm
        - url
        - key

        Omitting a field will delete the entire campaign.
        """

        # simple case: delete entire profile
        if field is None:
            confirm = await ctx.prompt("Are you sure you want to delete your profile?")
            if confirm:
                query = "DELETE FROM roll20_campaigns WHERE id=$1;"
                await ctx.db.execute(query, ctx.author.id)
                await ctx.send('Successfully deleted profile.')
            else:
                await ctx.send('Aborting profile deletion.')
            return

        field = field.lower()

        valid_fields = ( 'title', 'gm', 'url', 'key' )

        if field not in valid_fields:
            return await ctx.send("I don't know what field you want me to delete here bub.")

        # a little intermediate case, basic field deletion:
        field_to_column = {
            'title': 'title',
            'gm': 'gm',
            'url': 'url',
            'key': 'key'
        }

        column = field_to_column.get(field)
        if column:
            query = f"UPDATE roll20_campaigns SET {column} = NULL WHERE id=$1;"
            await ctx.db.execute(query, ctx.author.id)
            return await ctx.send(f'Successfully deleted {field} field.')

def setup(bot):
    bot.add_cog(Campaign(bot))
