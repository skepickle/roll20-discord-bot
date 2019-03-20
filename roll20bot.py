#import time
#import shutil
#import re
import os
import sys
import getopt

import discord
from discord.ext import commands
import asyncio

import roll20decoder
import json

# Options parsing

token          = ''
journal        = ''
chrome_path    = ''

config = {
    'command_prefix': '!',
    'global_bot_admins': [],
    'guilds': {}
}

"""
   config = {
       'command_prefix': char,
       'global_bot_admins': [ str ],
       'guilds': {
           '__str:server_id__': {
               'name': str,
               'adminRole': str,
               'gamemasterRole': str,
               'playerRole': str,
               'handoutURL': str,
               'handoutKey': str,
               'handoutTimestamp': time and date,
               'handout': dict
           }
       },
       'users': {
           '__str:user_id__': {
               guilds: []
           }
       }
   }
"""

if ('DISCORD_TOKEN' in os.environ):
    token       = os.environ['DISCORD_TOKEN']
if ('ROLL20_JOURNAL' in os.environ):
    journal     = os.environ['ROLL20_JOURNAL']
if ('CHROMEDRIVER_PATH' in os.environ):
    chrome_path = os.environ['CHROMEDRIVER_PATH']
if ('GLOBAL_BOT_ADMINS' in os.environ):
    config['global_bot_admins'] = os.environ['GLOBAL_BOT_ADMINS'].split(':')

try:
    opts, args = getopt.getopt(sys.argv[1:], "ht:j:c:", ["token=", "journal=", "chrome="])
except getopt.GetoptError:
    print('roll20bot.py -t <Discord Token> -j <Roll20 Journal URL> -c <ChromeDriver Path>')
    sys.exit(1)
for opt, arg in opts:
    if opt == "-h":
        print('roll20bot.py -t <Discord Token> -j <Roll20 Journal URL> -c <ChromeDriver Path>')
        sys.exit(1)
    elif opt in ("-t", "--token"):
        token = arg
    elif opt in ("-j", "--journal"):
        journal = arg
    elif opt in ("-c", "--chrome"):
        chrome_path = arg

bot = commands.Bot(command_prefix=config['command_prefix'], description="Roll20Bot provides access to select character sheets in Roll20 games", pm_help=True)
#bot.pm_help = True;
#print(bot.__dict__)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    for server in bot.servers:
        print("    "+server.name+", "+server.id)
        config['guilds'][server.id] = {
            'name': server.name,
            'adminRole': '',
            'palyerRole': ''
        }
    print('------')

@bot.event
async def on_guild_join(guild):
    if guild.id not in config['guilds']:
        await bot.say(guild.id + " not in current guilds list")
        config['guilds'][guild.id] = {
            'name': guild.name,
            'adminsRole': '',
            'usersRole': ''
        }
    return

@bot.event
async def on_guild_remove(guild):
    if guild.id in config['guilds']:
        await bot.say(guild.id + " in current guilds list")
        config['guilds'].pop(guild.id, None)
    return

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    #if not message.content.startswith(config['command_prefix']):
    #    return
    #await bot.send_message(message.channel, 'Entering on_message()')
    #if (not message.content.startswith('!abc') and
    #    not message.content.startswith('!def')):
    #    await bot.send_message(message.channel, 'Not a command for me!')
    #if message.content.startswith('!test'):
    #    #env_str =os.environ
    #    await bot.send_message(message.channel, 'Test Command from {}'.format(message.author))
    #    counter = 0
    #    tmp = await bot.send_message(message.channel, 'Calculating messages...')
    #    async for log in bot.logs_from(message.channel, limit=100):
    #        if log.author == message.author:
    #            counter += 1
    #    await bot.edit_message(tmp, 'You have {} messages.\n{}'.format(counter, os.environ))
    #    return
    #elif message.content.startswith('!json'):
    #    tmp = await bot.send_message(message.channel, 'Retrieving Roll20 JSON...')
    #    #varJSON = json.loads(utf8_decode(xor_decrypt('SUPER!SECRET~KEY',b64_decode(get_roll20_json()))))
    #    varJSON = Roll20BridgeDecoder.decode_roll20_journal(journal,'SUPER!SECRET~KEY')
    #    await bot.edit_message(tmp, 'The roll20 handout json = {}'.format(json.dumps(varJSON, indent=2, sort_keys=True))[0:2000])
    #elif message.content.startswith('!sleep'):
    #    await asyncio.sleep(5)
    #    await bot.send_message(message.channel, 'Done sleeping')
    await bot.process_commands(message)

@bot.command(pass_context=True, name='characters')
async def _discordbot_characters(ctx):
    pass

@bot.command(pass_context=True, name='sleep')
async def _discordbot_sleep(ctx):
    await asyncio.sleep(5)
    await bot.say('Done sleeping')

@bot.command(pass_context=True, name='test', description='DESCRIPTION BLAH BLAH', brief='print env vars', help='Print out server-side environment variables')
async def _discordbot_test(ctx, arg_1='1', arg_2='2'):
    await bot.say('Test Command from {}'.format(str(ctx.message.author)))
    counter = 0
    tmp = await bot.say('Calculating messages...')
    async for log in bot.logs_from(ctx.message.channel, limit=100):
        if log.author == ctx.message.author:
            counter += 1
    await bot.edit_message(tmp, 'You have {} messages.\n{}'.format(counter, os.environ))

@bot.command(pass_context=True, name='json')
async def _discordbot_json(ctx):
    tmp = await bot.say('Retrieving Roll20 JSON {} ...'.format(journal))
    varJSON = roll20decoder.decode_roll20_journal(chrome_path, journal, 'SUPER!SECRET~KEY')
    #await bot.say('The roll20 handout json = {}'.format(json.dumps(varJSON, indent=2, sort_keys=True))[0:2000])
    await bot.edit_message(tmp, 'The roll20 handout json = {}'.format(json.dumps(varJSON, indent=2, sort_keys=True))[0:2000])
    await bot.say('**attributes:**\n{}'.format(', '.join(varJSON['siliceous#5311']['Chirk Chorster']['attributes'].keys()))[0:2000])

####################
# Global Bot Administration
####################

# Global bot admins are defined at deployment-time of the bot, and cannot be modified live.

def is_global_bot_admin(ctx):
    return str(ctx.message.author) in config['global_bot_admins']

@bot.group(pass_context=True, name='global', hidden=True, description='The global group of commands allow for administration of Roll20Bot globally')
async def _discordbot_global(ctx):
    if ctx.message.server != None:
        await bot.say('The **global** configuration command-group must be initiated from a private-message, not a guild channel.')
    if not is_global_bot_admin(ctx):
        return

@_discordbot_global.command(pass_context=True, name='guilds', brief='List guilds using this bot', description='List guilds that are currently have Roll20Bot added.', help='This command does not accept any arguments.')
async def _discordbot_global_guilds(ctx):
    if ctx.message.server != None:
        return
    if not is_global_bot_admin(ctx):
        return
    s = ''
    if len(config['guilds']) == 0:
        s = 'There are no Discord guilds configured.'
    else:
        s = "The following Discord guilds are configured:\n"
        for key, value in config['guilds'].items():
            s += "    " + key + " => " + value['name'] + "\n"
    await bot.say(s)

####################
# Guild Bot Administration
####################

# Guild owners should always be able to modify these configurations
# If a role is defined for administrators, then the members of that role will also be able to modify guild configs

def is_guild_admin(ctx):
    if ctx.message.server == None:
        return False
    if ctx.message.author == ctx.message.server.owner:
        return True
    # TODO Also check admin role on guild...
    return False

@bot.group(pass_context=True, name='guild', hidden=True)
async def _discordbot_guild(ctx):
    if ctx.message.server == None:
        await bot.say('The **guild** configuration command-group must be initiated from a guild channel, not a private-message.')
    if not is_guild_admin(ctx):
        return
    if ctx.invoked_subcommand is None:
        await bot.say('Print !guild usage here.')

@_discordbot_guild.command(pass_context=True, name='handout')
async def _discordbot_guild_handout(ctx, url=None: str, key=None: str):
    if ctx.message.server == None:
        return
    if not is_guild_admin(ctx):
        return
    if (url == None) and (key == None):
        s = 'Current guild handout configuration:\n'
        s += '- url: '
        if 'handoutURL' in config['guilds'][ctx.message.server.id]:
            s += config['guilds'][ctx.message.server.id]['handoutURL']
        else:
            s += 'UNDEFINED'
        s += '\n- key: '
        if 'handoutKey' in config['guilds'][ctx.message.server.id]:
            s += config['guilds'][ctx.message.server.id]['handoutKey']
        else:
            s += 'UNDEFINED'
       await bot.say(s)
       return
    if (url != None):
        config['guilds'][ctx.message.server.id]['handoutURL'] = url
    if (key != None):
        config['guilds'][ctx.message.server.id]['handoutKey'] = key

bot.run(token)
