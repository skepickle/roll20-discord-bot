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
    'admins': [],
    'servers': {}
}

"""
   config = {
       'command_prefix': char,
       'admins': [ str ],
       'servers': {
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
               servers: []
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
if ('BOT_ADMINS' in os.environ):
    config['admins'] = os.environ['BOT_ADMINS'].split(':')

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

bot = commands.Bot(command_prefix=config['command_prefix'], help_command=discord.ext.commands.DefaultHelpCommand(dm_help=True), description="blah blah")

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    for server in bot.servers:
        print("    "+server.name+", "+server.id)
        config['servers'][server.id] = {
            'name': server.name,
            'adminRole': '',
            'palyerRole': ''
        }
    print('------')

@bot.event
async def on_guild_join(guild):
    if guild.id not in config['servers']:
        await bot.say(guild.id + "not in current servers list")
        config['servers'][guild.id] = {
            'name': guild.name,
            'adminsRole': '',
            'usersRole': ''
        }
    return

@bot.event
async def on_guild_remove(guild):
    if guild.id in config['servers']:
        await bot.say(guild.id + " in current servers list")
        config['servers'].pop(guild.id, None)
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

@bot.command(pass_context=True, name='test', description='DESCRIPTION BLAH BLAH', brief='print env vars', help='Print out server side environment variables')
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
# Bot Administration Functions
####################

# Bot admins are defined at deployment of the bot, and cannot be modified live.

def is_bot_admin(ctx):
    return str(ctx.message.author) in config['admins']

@bot.group(pass_context=True, name='admin')
async def _discordbot_admin(ctx):
    if not is_bot_admin(ctx):
        return
    if ctx.invoked_subcommand is None:
        await bot.say('TODO: Print !admin usage here.')

@_discordbot_admin.command(pass_context=True, name='list')
async def _discordbot_admin_list(ctx):
    if not is_bot_admin(ctx):
        return
    s = ''
    if len(config['servers']) == 0:
        s = 'There are no Discord servers configured.'
    else:
        s = "The following Discord servers are configured:\n"
        for key, value in config['servers'].items():
            s += "    " + key + " => " + value['name'] + "\n"
    await bot.say(s)

####################
# Server Configuration Functions
####################

# Server Owners should always be able to modify these configurations
# If a role is defined for administrators, then the members of that role will also be able to modify server configs

def is_server_admin(ctx):
    if ctx.message.server == None:
        return False
    if ctx.message.author == ctx.message.server.owner:
        return True
    # TODO Also check admin role on server...
    return False

@bot.group(pass_context=True, name='config')
async def _discordbot_config(ctx):
    if not is_server_admin(ctx):
        return
    if ctx.invoked_subcommand is None:
        await bot.say('Print !config usage here.')

@_discordbot_config.command(pass_context=True, name='journal')
async def _discordbot_config_journal(ctx):
    if not is_server_admin(ctx):
        return
    s = ''
    if len(config['servers']) == 0:
        s = 'There are no Discord servers configured.'
    else:
        s = "The following Discord servers are configured:\n"
        for key, value in config['servers'].items():
            s += "    " + key + " => " + value['name'] + "\n"
    await bot.say(s)

bot.run(token)
