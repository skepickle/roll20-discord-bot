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
    'servers': {},
    'admins': []
}

if ('DISCORD_TOKEN' in os.environ):
    token       = os.environ['DISCORD_TOKEN']
if ('ROLL20_JOURNAL' in os.environ):
    journal     = os.environ['ROLL20_JOURNAL']
if ('CHROMEDRIVER_PATH' in os.environ):
    chrome_path = os.environ['CHROMEDRIVER_PATH']
if ('GLOBAL_ADMINS' in os.environ):
    config['admins'] = os.environ['GLOBAL_ADMINS'].split(':')

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

bot = commands.Bot(command_prefix=config['command_prefix'], description="blah blah")

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
            'adminsRole': '',
            'usersRole': ''
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

@bot.command(pass_context=True, name='sleep')
async def _discordbot_sleep(ctx):
    await asyncio.sleep(5)
    await bot.say('Done sleeping')

@bot.command(pass_context=True, name='test')
async def _discordbot_test(ctx):
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
    varJSON = roll20decoder.Roll20Decoder.decode_roll20_journal(chrome_path, journal,'SUPER!SECRET~KEY')
    #await bot.say('The roll20 handout json = {}'.format(json.dumps(varJSON, indent=2, sort_keys=True))[0:2000])
    await bot.edit_message(tmp, 'The roll20 handout json = {}'.format(json.dumps(varJSON, indent=2, sort_keys=True))[0:2000])

####################
# Global Administration Functions
####################

# Global admins are defined at deployment of the bot, and cannot be modified live.

@bot.group(pass_context=True, name='admin')
async def _discordbot_admin(ctx):
    await bot.say('pew pew:')
    if ctx.invoked_subcommand is None:
        await bot.say(str(ctx.message.author) + ' in '+ ':'.join(config['admins']) + " ?")
        if str(ctx.message.author) not in config['admins']:
            await bot.say('go away! (admin)')
            return
        await bot.say('Print !admin usage here.')

@_discordbot_admin.command(pass_context=True, name='list')
async def _discordbot_admin_list(ctx):
    if str(ctx.message.author) not in config['admins']:
        await bot.say('go away! (admin list)')
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

@bot.group(pass_context=True, name='config')
async def _discordbot_config(ctx):
    if ctx.invoked_subcommand is None:
        await bot.say('Print !config usage here.')

@_discordbot_config.command(pass_context=True, name='journal')
async def _discordbot_config_journal(ctx):
    s = ''
    if len(config['servers']) == 0:
        s = 'There are no Discord servers configured.'
    else:
        s = "The following Discord servers are configured:\n"
        for key, value in config['servers'].items():
            s += "    " + key + " => " + value['name'] + "\n"
    await bot.say(s)

bot.run(token)
