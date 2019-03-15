from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import json
import shutil
import re
import os

import sys
import getopt

import discord
from discord.ext import commands
import asyncio

# Options parsing

token       = ''
journal     = ''
chrome_path = ''

config = {}

if ('DISCORD_TOKEN' in os.environ):
    token       = os.environ['DISCORD_TOKEN']
if ('ROLL20_JOURNAL' in os.environ):
    journal     = os.environ['ROLL20_JOURNAL']
if ('CHROMEDRIVER_PATH' in os.environ):
    chrome_path = os.environ['CHROMEDRIVER_PATH']

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

class Roll20BridgeDecoder:

    #Currently don't need a constructor
    #def __init__(self):
    #    print("This is the constructor method.")

    @classmethod
    def b64_decode(cls,data):
        b64_table = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
        i = 0
        result = []
        if (data is None):
          return data
        data += ""
        while True:
            h1 = b64_table.index(data[i])
            h2 = b64_table.index(data[i+1])
            h3 = b64_table.index(data[i+2])
            h4 = b64_table.index(data[i+3])
            i += 4
            bits = h1 << 18 | h2 << 12 | h3 << 6 | h4
            o1 = bits >> 16 & 0xFF
            o2 = bits >> 8 & 0xFF
            o3 = bits & 0xFF
            result.append(o1)
            if (h3 != 64):
                result.append(o2)
                if (h4 != 64):
                    result.append(o3)
            if (i >= len(data)):
                break
        return result

    @classmethod
    def xor_decrypt(cls,key, data):
        result = []
        for i, datum in enumerate(data):
            result.append(datum ^ ord(key[i % len(key)]))
        return "".join(map(chr,result))

    @classmethod
    def utf8_decode(cls,utftext):
        string = ""
        i = 0
        c1 = 0
        c2 = 0
        c3 = 0
        while i < len(utftext):
            c1 = ord(utftext[i])
            if c1 < 128:
                string += chr(c1)
                i += 1
            elif (c1 > 191) and (c1 < 224):
                c2 = ord(utftext[i+1])
                string += chr(((c1 & 31) << 6) | (c2 & 63))
                i += 2
            else:
                c2 = ord(utftext[i+1])
                c3 = ord(utftext[i+2])
                string += chr(((c1 & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63))
                i += 3
        return string

    @classmethod
    def decode_roll20_journal(cls,journal,key):

        #Define webdriver with path
        options = Options()
        options.headless = True
        driver = webdriver.Chrome(executable_path=chrome_path, chrome_options=options)

        journal_notes = ""
        try:

            roll20search = re.search('Roll20: Online virtual tabletop', driver.title)

            #If the title of the page already exists (ie, the window is open), don't open a new one
            if roll20search:

                #Get the text from HTML element
                text = driver.find_element_by_xpath("""//*[@id="openpages"]/div/span""")
                journal_notes = text.text

            #if chrome window is not open
            else:

                #Open URL to roll20 handout
                driver.get(journal)

                time.sleep(2)
                while not journal_notes:
                    #Get the text from HTML element
                    text = driver.find_element_by_xpath("""//*[@id="openpages"]/div/span""")
                    journal_notes = text.text
                    time.sleep(0.5)

        #If you can't find the chrome window, raise exception and exit script
        except Exception as e:
            print(str(e))
            #Quit driver
            driver.quit()
            #Exit script
            exit()

        varJSON = json.loads(cls.utf8_decode(cls.xor_decrypt(key,cls.b64_decode(journal_notes))))

        return varJSON


#client = discord.Client()
client = commands.Bot(command_prefix='!', description="blah blah")

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    for server in client.servers:
        print(server.name+", "+server.id+"\n")
    print('------')

@client.event
async def on_message(message):
    if not message.content.startswith('!'):
        return
    await client.send_message(message.channel, 'Entering on_message()')
    if (not message.content.startswith('!test') and
        not message.content.startswith('!json') and
        not message.content.startswith('!sleep')):
        await client.send_message(message.channel, 'Not a command for me!')
        return
    if message.content.startswith('!test'):
        #env_str =os.environ
        await client.send_message(message.channel, 'Test Command from {}'.format(message.author))
        counter = 0
        tmp = await client.send_message(message.channel, 'Calculating messages...')
        async for log in client.logs_from(message.channel, limit=100):
            if log.author == message.author:
                counter += 1
        await client.edit_message(tmp, 'You have {} messages.\n{}'.format(counter, os.environ))
    elif message.content.startswith('!json'):
        tmp = await client.send_message(message.channel, 'Retrieving Roll20 JSON...')
        #varJSON = json.loads(utf8_decode(xor_decrypt('SUPER!SECRET~KEY',b64_decode(get_roll20_json()))))
        varJSON = Roll20BridgeDecoder.decode_roll20_journal(journal,'SUPER!SECRET~KEY')
        await client.edit_message(tmp, 'The roll20 handout json = {}'.format(json.dumps(varJSON, indent=2, sort_keys=True))[0:2000])
    #elif message.content.startswith('!sleep'):
    #    await asyncio.sleep(5)
    #    await client.send_message(message.channel, 'Done sleeping')
    await bot.process_commands(message)

@client.command()
async def sleep():
    await asyncio.sleep(5)
    await client.say('Done sleeping')

client.run(token)
