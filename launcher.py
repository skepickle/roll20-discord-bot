import sys
import click
import logging
import asyncio
import asyncpg
import discord
import importlib
import contextlib

from bot import Roll20Bot, initial_extensions
from cogs.utils.db import Table

from pathlib import Path

import config
import traceback

try:
    import uvloop
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

#######################
####
####import os
####import getopt
####from discord.ext import commands
####import roll20bridge
#####import roll20sheet
####import json
####
####if __name__ != "__main__":
####    print("ERROR: bot.py must be executed as the top-level code.")
####    sys.exit(1)
####
####old_config = {
####    'command_prefix': '!',
####    'global_bot_admins': [],
####    'guilds': {}
####}
####
####"""
####   config = {
####       'command_prefix': char,
####       'global_bot_admins': [ str ],
####       'guilds': {
####           '__str:server_id__': {
####               'name': str,
####               'adminRole': str,
####               'gamemasterRole': str,
####               'playerRole': str,
####               'bridgeURL': str,
####               'bridgeKey': str,
####               'bridgeTimestamp': time and date,
####               'characters': Roll20Character[]
####           }
####       },
####       'players': {
####           '__str:user_id__': {
####               'guilds': [],
####               'characters': []
####           }
####       }
####   }
####"""
####
####bot = commands.Bot(command_prefix=old_config['command_prefix'], description="Roll20Bot provides access to select character sheets in Roll20 games", pm_help=True)
####
####@bot.event
####async def on_ready():
####    print('Logged in as')
####    print(bot.user.name)
####    print(bot.user.id)
####    print('------')
####    for guild in bot.guilds:
####        print("    "+guild.name+", "+str(guild.id))
####        old_config['guilds'][guild.id] = {
####            'name': guild.name
####        }
####    print('------')
####
####@bot.event
####async def on_guild_join(guild):
####    if guild.id not in old_config['guilds']:
####        #await ctx.channel.send(guild.id + " not in current guilds list")
####        old_config['guilds'][guild.id] = {
####            'name': guild.name,
####            'adminsRole': '',
####            'usersRole': ''
####        }
####    return
####
####@bot.event
####async def on_guild_remove(guild):
####    if guild.id in old_config['guilds']:
####        #await ctx.channel.send(guild.id + " in current guilds list")
####        old_config['guilds'].pop(guild.id, None)
####    return
####
####@bot.event
####async def on_message(message):
####    if message.author.bot:
####        return
####    #if not message.content.startswith(old_config['command_prefix']):
####    #    return
####    #await bot.send_message(message.channel, 'Entering on_message()')
####    #if (not message.content.startswith('!abc') and
####    #    not message.content.startswith('!def')):
####    #    await bot.send_message(message.channel, 'Not a command for me!')
####    #if message.content.startswith('!test'):
####    #    #env_str =os.environ
####    #    await bot.send_message(message.channel, 'Test Command from {}'.format(message.author))
####    #    counter = 0
####    #    tmp = await bot.send_message(message.channel, 'Calculating messages...')
####    #    async for log in bot.logs_from(message.channel, limit=100):
####    #        if log.author == message.author:
####    #            counter += 1
####    #    await bot.edit_message(tmp, 'You have {} messages.\n{}'.format(counter, os.environ))
####    #    return
####    #elif message.content.startswith('!json'):
####    #    tmp = await bot.send_message(message.channel, 'Retrieving Roll20 JSON...')
####    #    #varJSON = json.loads(utf8_decode(xor_decrypt(config.handout_key,b64_decode(get_roll20_json()))))
####    #    varJSON = Roll20BridgeDecoder.load_handout(config.chromedriver_path, config.handout_url, config.handout_key)
####    #    await bot.edit_message(tmp, 'The roll20 handout json = {}'.format(json.dumps(varJSON, indent=2, sort_keys=True))[0:2000])
####    #elif message.content.startswith('!sleep'):
####    #    await asyncio.sleep(5)
####    #    await bot.send_message(message.channel, 'Done sleeping')
####    await bot.process_commands(message)
####
####@bot.command(name='characters')
####async def _discordbot_characters(ctx):
####    pass
####
####@bot.command(name='sleep')
####async def _discordbot_sleep(ctx):
####    await asyncio.sleep(1)
####    await ctx.channel.send('Done sleeping')
####
####@bot.command(name='json')
####async def _discordbot_json(ctx):
####    tmp = await ctx.channel.send('Retrieving Roll20 JSON {} ...'.format(config.handout_url))
####    varJSON = roll20bridge.load_handout(config.chromedriver_path, config.handout_url, config.handout_key)
####    if varJSON == None:
####        await tmp.edit(content='Could not load Roll20 bridge handout at {}'.format(config.handout_url))
####        return
####    #await ctx.channel.send('The roll20 handout json = {}'.format(json.dumps(varJSON, indent=2, sort_keys=True))[0:2000])
####    #await bot.edit_message(tmp, '**Roll20 bridge handout loaded:**\n{}'.format(json.dumps(varJSON, indent=2, sort_keys=True))[0:2000])
####    await tmp.edit(content='**attributes:**\n{}'.format(', '.join(varJSON['siliceous#5311']['Chirk Chorster']['attributes'].keys()))[0:2000])
####
########################
##### Global Bot Administration
########################
####
##### Global bot admins are defined at deployment-time of the bot, and cannot be modified live.
####
####def is_global_bot_admin(ctx):
####    return str(ctx.message.author) in old_config['global_bot_admins']
####
####@bot.group(name='global', hidden=True, description='The global group of commands allow for administration of Roll20Bot globally')
####async def _discordbot_global(ctx):
####    if ctx.guild != None:
####        await ctx.channel.send('The **global** configuration command-group must be initiated from a private-message, not a guild channel.')
####    if not is_global_bot_admin(ctx):
####        return
####
####@_discordbot_global.command(name='test', description='DESCRIPTION BLAH BLAH', brief='print env vars', help='Print out server-side environment variables')
####async def _discordbot_global_test(ctx, arg_1='1', arg_2='2'):
####    if ctx.guild != None:
####        return
####    if not is_global_bot_admin(ctx):
####        return
####    counter = 0
####    tmp = await ctx.channel.send('Calculating messages...')
####    #async for log in bot.logs_from(ctx.message.channel, limit=100):
####    #    if log.author == ctx.message.author:
####    #        counter += 1
####    await tmp.edit(content='{}'.format(os.environ))
####
####@_discordbot_global.command(name='guilds', brief='List guilds using this bot', description='List guilds that are currently have Roll20Bot added.', help='This command does not accept any arguments.')
####async def _discordbot_global_guilds(ctx):
####    if ctx.guild != None:
####        return
####    if not is_global_bot_admin(ctx):
####        return
####    s = ''
####    if len(old_config['guilds']) == 0:
####        s = 'There are no Discord guilds configured.'
####    else:
####        s = "The following Discord guilds are configured:\n"
####        for key, value in old_config['guilds'].items():
####            s += "    " + str(key) + " => " + value['name'] + "\n"
####    await ctx.channel.send(s)
####
########################
##### Guild Bot Administration
########################
####
##### Guild owners should always be able to modify these configurations
##### If a role is defined for administrators, then the members of that role will also be able to modify guild configs
####
####def is_guild_admin(ctx):
####    if ctx.guild == None:
####        return False
####    if ctx.message.author == ctx.guild.owner:
####        return True
####    # TODO Also check admin role on guild...
####    return False
####
####@bot.group(name='guild', hidden=True)
####async def _discordbot_guild(ctx):
####    if ctx.guild == None:
####        await ctx.channel.send('The **guild** configuration command-group must be initiated from a guild channel, not a private-message.')
####    if not is_guild_admin(ctx):
####        return
####    if ctx.invoked_subcommand is None:
####        await ctx.channel.send('Print !guild usage here.')
####
####@_discordbot_guild.command(name='bridge')
####async def _discordbot_guild_bridge(ctx, url=None, key=None):
####    if ctx.guild == None:
####        return
####    if not is_guild_admin(ctx):
####        return
####    if (url == None) and (key == None):
####        s = 'Current guild bridge configuration:\n'
####        s += '- url: '
####        if 'bridgeURL' in old_config['guilds'][ctx.guild.id]:
####            s += old_config['guilds'][ctx.guild.id]['bridgeURL']
####        else:
####            s += 'UNDEFINED'
####        s += '\n- key: '
####        if 'bridgeKey' in old_config['guilds'][ctx.guild.id]:
####            s += old_config['guilds'][ctx.guild.id]['bridgeKey']
####        else:
####            s += 'UNDEFINED'
####        await ctx.channel.send(s)
####        return
####    if (url != None):
####        old_config['guilds'][ctx.guild.id]['bridgeURL'] = url
####    if (key != None):
####        old_config['guilds'][ctx.guild.id]['bridgeKey'] = key
####
#######################

@contextlib.contextmanager
def setup_logging():
    try:
        # __enter__
        logging.getLogger('discord').setLevel(logging.INFO)
        logging.getLogger('discord.http').setLevel(logging.WARNING)

        log = logging.getLogger()
        log.setLevel(logging.INFO)
        handler = logging.FileHandler(filename='rdanny.log', encoding='utf-8', mode='w')
        dt_fmt = '%Y-%m-%d %H:%M:%S'
        fmt = logging.Formatter('[{asctime}] [{levelname:<7}] {name}: {message}', dt_fmt, style='{')
        handler.setFormatter(fmt)
        log.addHandler(handler)

        yield
    finally:
        # __exit__
        handlers = log.handlers[:]
        for hdlr in handlers:
            hdlr.close()
            log.removeHandler(hdlr)

def run_bot():
    loop = asyncio.get_event_loop()
    log = logging.getLogger()

    try:
        pool = loop.run_until_complete(Table.create_pool(config.postgresql, command_timeout=60))
    except Exception as e:
        click.echo('Could not set up PostgreSQL. Exiting.', file=sys.stderr)
        log.exception('Could not set up PostgreSQL. Exiting.')
        return

    bot = Roll20Bot()
    bot.pool = pool
    bot.run()

@click.group(invoke_without_command=True, options_metavar='[options]')
@click.pass_context
def main(ctx):
    """Launches the bot."""
    if ctx.invoked_subcommand is None:
        loop = asyncio.get_event_loop()
        with setup_logging():
            run_bot()
####    bot.run(config.token)

@main.group(short_help='database stuff', options_metavar='[options]')
def db():
    pass

@db.command(short_help='initialises the databases for the bot', options_metavar='[options]')
@click.argument('cogs', nargs=-1, metavar='[cogs]')
@click.option('-q', '--quiet', help='less verbose output', is_flag=True)
def init(cogs, quiet):
    """This manages the migrations and database creation system for you."""

    run = asyncio.get_event_loop().run_until_complete
    try:
        run(Table.create_pool(config.postgresql))
    except Exception:
        click.echo(f'Could not create PostgreSQL connection pool.\n{traceback.format_exc()}', err=True)
        return

    if not cogs:
        cogs = initial_extensions
    else:
        cogs = [f'cogs.{e}' if not e.startswith('cogs.') else e for e in cogs]

    for ext in cogs:
        try:
            importlib.import_module(ext)
        except Exception:
            click.echo(f'Could not load {ext}.\n{traceback.format_exc()}', err=True)
            return

    for table in Table.all_tables():
        try:
            created = run(table.create(verbose=not quiet, run_migrations=False))
        except Exception:
            click.echo(f'Could not create {table.__tablename__}.\n{traceback.format_exc()}', err=True)
        else:
            if created:
                click.echo(f'[{table.__module__}] Created {table.__tablename__}.')
            else:
                click.echo(f'[{table.__module__}] No work needed for {table.__tablename__}.')

    click.echo(f'Wait for completion', err=False)
    asyncio.sleep(3)
    click.echo(f'db init complete', err=False)
    while True:
        asyncio.sleep(10)

db.command(short_help='migrates the databases')
@click.argument('cog', nargs=1, metavar='[cog]')
@click.option('-q', '--quiet', help='less verbose output', is_flag=True)
@click.pass_context
def migrate(ctx, cog, quiet):
    """Update the migration file with the newest schema."""

    if not cog.startswith('cogs.'):
        cog = f'cogs.{cog}'

    try:
        importlib.import_module(cog)
    except Exception:
        click.echo(f'Could not load {ext}.\n{traceback.format_exc()}', err=True)
        return

    def work(table, *, invoked=False):
        try:
            actually_migrated = table.write_migration()
        except RuntimeError as e:
            click.echo(f'Could not migrate {table.__tablename__}: {e}', err=True)
            if not invoked:
                click.confirm('do you want to create the table?', abort=True)
                ctx.invoke(init, cogs=[cog], quiet=quiet)
                work(table, invoked=True)
            sys.exit(-1)
        else:
            if actually_migrated:
                click.echo(f'Successfully updated migrations for {table.__tablename__}.')
            else:
                click.echo(f'Found no changes for {table.__tablename__}.')

    for table in Table.all_tables():
        work(table)

    click.echo(f'Done migrating {cog}.')

async def apply_migration(cog, quiet, index, *, downgrade=False):
    try:
        pool = await Table.create_pool(config.postgresql)
    except Exception:
        click.echo(f'Could not create PostgreSQL connection pool.\n{traceback.format_exc()}', err=True)
        return

    if not cog.startswith('cogs.'):
        cog = f'cogs.{cog}'

    try:
        importlib.import_module(cog)
    except Exception:
        click.echo(f'Could not load {cog}.\n{traceback.format_exc()}', err=True)
        return

    async with pool.acquire() as con:
        tr = con.transaction()
        await tr.start()
        for table in Table.all_tables():
            try:
                await table.migrate(index=index, downgrade=downgrade, verbose=not quiet, connection=con)
            except RuntimeError as e:
                click.echo(f'Could not migrate {table.__tablename__}: {e}', err=True)
                await tr.rollback()
                break
        else:
            await tr.commit()

@db.command(short_help='upgrades from a migration')
@click.argument('cog', nargs=1, metavar='[cog]')
@click.option('-q', '--quiet', help='less verbose output', is_flag=True)
@click.option('--index', help='the index to use', default=-1)
def upgrade(cog, quiet, index):
    """Runs an upgrade from a migration"""
    run = asyncio.get_event_loop().run_until_complete
    run(apply_migration(cog, quiet, index))

@db.command(short_help='downgrades from a migration')
@click.argument('cog', nargs=1, metavar='[cog]')
@click.option('-q', '--quiet', help='less verbose output', is_flag=True)
@click.option('--index', help='the index to use', default=-1)
def downgrade(cog, quiet, index):
    """Runs an downgrade from a migration"""
    run = asyncio.get_event_loop().run_until_complete
    run(apply_migration(cog, quiet, index, downgrade=True))

async def remove_databases(pool, cog, quiet):
    async with pool.acquire() as con:
        tr = con.transaction()
        await tr.start()
        for table in Table.all_tables():
            try:
                await table.drop(verbose=not quiet, connection=con)
            except RuntimeError as e:
                click.echo(f'Could not drop {table.__tablename__}: {e}', err=True)
                await tr.rollback()
                break
            else:
                click.echo(f'Dropped {table.__tablename__}.')
        else:
            await tr.commit()
            click.echo(f'successfully removed {cog} tables.')

@db.command(short_help="removes a cog's table", options_metavar='[options]')
@click.argument('cog',  metavar='<cog>')
@click.option('-q', '--quiet', help='less verbose output', is_flag=True)
def drop(cog, quiet):
    """This removes a database and all its migrations.
    You must be pretty sure about this before you do it,
    as once you do it there's no coming back.
    Also note that the name must be the database name, not
    the cog name.
    """

    run = asyncio.get_event_loop().run_until_complete
    click.confirm('do you really want to do this?', abort=True)

    try:
        pool = run(Table.create_pool(config.postgresql))
    except Exception:
        click.echo(f'Could not create PostgreSQL connection pool.\n{traceback.format_exc()}', err=True)
        return

    if not cog.startswith('cogs.'):
        cog = f'cogs.{cog}'

    try:
        importlib.import_module(cog)
    except Exception:
        click.echo(f'Could not load {cog}.\n{traceback.format_exc()}', err=True)
        return

    run(remove_databases(pool, cog, quiet))

@main.command(short_help='migrates from JSON files')
@click.argument('cogs', nargs=-1)
@click.pass_context
def convertjson(ctx, cogs):
    """This migrates our older JSON files to PostgreSQL
    Note, this deletes all previous entries in the table
    so you can consider this to be a destructive decision.
    Do not pass in cog names with "cogs." as a prefix.
    This also connects us to Discord itself so we can
    use the cache for our migrations.
    The point of this is just to do some migration of the
    data from v3 -> v4 once and call it a day.
    """

    import data_migrators

    run = asyncio.get_event_loop().run_until_complete

    if not cogs:
        to_run = [(getattr(data_migrators, attr), attr.replace('migrate_', ''))
                  for attr in dir(data_migrators) if attr.startswith('migrate_')]
    else:
        to_run = []
        for cog in cogs:
            try:
                elem = getattr(data_migrators, 'migrate_' + cog)
            except AttributeError:
                click.echo(f'invalid cog name given, {cog}.', err=True)
                return

            to_run.append((elem, cog))

    async def make_pool():
        return await asyncpg.create_pool(config.postgresql)

    try:
        pool = run(make_pool())
    except Exception:
        click.echo(f'Could not create PostgreSQL connection pool.\n{traceback.format_exc()}', err=True)
        return

    client = discord.AutoShardedClient()

    @client.event
    async def on_ready():
        click.echo(f'successfully booted up bot {client.user} (ID: {client.user.id})')
        await client.logout()

    try:
        run(client.login(config.token))
        run(client.connect(reconnect=False))
    except:
        pass

    extensions = ['cogs.' + name for _, name in to_run]
    ctx.invoke(init, cogs=extensions)

    for migrator, _ in to_run:
        try:
            run(migrator(pool, client))
        except Exception:
            click.echo(f'[error] {migrator.__name__} has failed, terminating\n{traceback.format_exc()}', err=True)
            return
        else:
            click.echo(f'[{migrator.__name__}] completed successfully')

if __name__ == '__main__':
    main()