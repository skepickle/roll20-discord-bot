from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import json
import shutil
import re

import sys
import getopt

import discord
import asyncio

token = ''
journal = ''
chrome_path = ''

try:
    opts, args = getopt.getopt(sys.argv[1:], "ht:j:c:", ["token=", "journal=", "chrome="])
except getopt.GetoptError:
    print('roll20bot.py -t <Discord Token> -j <Roll20 Journal URL>')
    sys.exit(1)
for opt, arg in opts:
    print("opt = ", opt)
    print("arg = ", arg)
    if opt == "-h":
        print('roll20bot.py -t <Discord Token> -j <Roll20 Journal URL>')
        sys.exit(1)
    elif opt in ("-t", "--token"):
        token = arg
    elif opt in ("-j", "--journal"):
        journal = arg
    elif opt in ("-c", "--chrome"):
        chrome_path = arg
print("left over args = ", args)
print("token   is ", token)
print("journal is ", journal)
print("chrome  is ", chrome_path)

def b64_decode(data):
    b64_table = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
    i = 0
    result = []
    if (data is None):
      return data
    data += ""
    while True:
        h1 = b64_table.index(data[i])
        i += 1
        h2 = b64_table.index(data[i])
        i += 1
        h3 = b64_table.index(data[i])
        i += 1
        h4 = b64_table.index(data[i])
        i += 1
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

def xor_decrypt(key, data):
    result = []
    for im datum in enumerate(data):
        result.append(datum ^ ord(key[i % len(key)]))
    return "".join(map(chr,result))

def get_roll20_json():

    #Path to the journal containing the JSON of the players
    path_to_external_journal = journal

    #Define webdriver with path
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(executable_path=chrome_path, chrome_options=options)

    varJSON = ""
    #Try to run script
    try:
        
        roll20search = re.search('Roll20: Online virtual tabletop', driver.title)
    
        #If the title of the page already exists (ie, the window is open), don't open a new one
        if roll20search:
        
            #Get the text from HTML element
            text = driver.find_element_by_xpath("""//*[@id="openpages"]/div/span""")
            varJSON = text.text

        #if chrome window is not open
        else:
        
            #Open URL to roll20 handout
            driver.get(path_to_external_journal)
            
            time.sleep(2)
            while not varJSON:
                #Get the text from HTML element
                text = driver.find_element_by_xpath("""//*[@id="openpages"]/div/span""")
                #print(text.text)
                varJSON = text.text
                time.sleep(0.5)         

        
    #If you can't find the chrome window, raise exception and exit script
    except Exception as e:
        print(str(e))
        #Quit driver
        driver.quit()
        #Exit script
        exit()

    return varJSON


client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    if message.content.startswith('!test'):
        await client.send_message(message.channel, 'Test Command from {}'.format(message.author))
        counter = 0
        tmp = await client.send_message(message.channel, 'Calculating messages...')
        async for log in client.logs_from(message.channel, limit=100):
            if log.author == message.author:
                counter += 1

        await client.edit_message(tmp, 'You have {} messages.'.format(counter))
    elif message.content.startswith('!json'):
        tmp = await client.send_message(message.channel, 'Retrieving Roll20 JSON...')
        json = str(xor_decrypt('SUPER!SECRET~KEY', b64_decode(get_roll20_json())))
        await client.edit_message(tmp, 'The roll20 handout json = {}'.format(json)[0:1000])
    elif message.content.startswith('!sleep'):
        await asyncio.sleep(5)
        await client.send_message(message.channel, 'Done sleeping')

client.run(token)
