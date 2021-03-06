from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import re
import time

#import roll20sheet

##############################
# Define utility methods
##############################

def decode_base64(base64_data):
    base64_table = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
    i = 0
    data = []
    if (base64_data is None):
      return base64_data
    base64_data += ""   # TODO Is this step necessary?
    while True:
        h1 = base64_table.index(base64_data[i])
        h2 = base64_table.index(base64_data[i+1])
        h3 = base64_table.index(base64_data[i+2])
        h4 = base64_table.index(base64_data[i+3])
        i += 4
        bits = h1 << 18 | h2 << 12 | h3 << 6 | h4
        o1 = bits >> 16 & 0xFF
        o2 = bits >> 8 & 0xFF
        o3 = bits & 0xFF
        data.append(o1)
        if (h3 != 64):
            data.append(o2)
            if (h4 != 64):
                data.append(o3)
        if (i >= len(base64_data)):
            break
    return data

def decrypt(key, enc_data):
    dec_data = []
    for i, datum in enumerate(enc_data):
        dec_data.append(datum ^ ord(key[i % len(key)]))
    return "".join(map(chr,dec_data))

def decode_utf8(utf_text):
    unicode_text = ""
    i = 0
    c1 = 0
    c2 = 0
    c3 = 0
    while i < len(utf_text):
        c1 = ord(utf_text[i])
        if c1 < 128:
            unicode_text += chr(c1)
            i += 1
        elif (c1 > 191) and (c1 < 224):
            c2 = ord(utf_text[i+1])
            unicode_text += chr(((c1 & 31) << 6) | (c2 & 63))
            i += 2
        else:
            c2 = ord(utf_text[i+1])
            c3 = ord(utf_text[i+2])
            unicode_text += chr(((c1 & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63))
            i += 3
    return unicode_text

##############################
# Define method to load handout from URL
##############################

def load_handout(chrome,handout_url,handout_key):

    #Define webdriver with path
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(executable_path=chrome, chrome_options=options)

    handout_url_notes = ""
    try:

        roll20search = re.search('Roll20: Online virtual tabletop', driver.title)

        #If the title of the page already exists (ie, the window is open), don't open a new one
        if roll20search:

            #Get the text from HTML element
            text = driver.find_element_by_xpath("""//*[@id="openpages"]/div/span""")
            handout_url_notes = text.text

        #if chrome window is not open
        else:

            #Open URL to roll20 handout
            driver.get(handout_url)

            time.sleep(2)
            while not handout_url_notes:
                #Get the text from HTML element
                text = driver.find_element_by_xpath("""//*[@id="openpages"]/div/span""")
                handout_url_notes = text.text
                time.sleep(0.5)

    #If you can't find the chrome window, raise exception and return None
    except Exception as e:
        print(str(e))
        #Quit driver
        driver.quit()
        #Exit script
        return None

    driver.quit()
    return json.loads(decode_utf8(decrypt(handout_key,decode_base64(handout_url_notes))))

##############################
# If being used as top-level code, parse command-line arguments and perform some useful actions that could be used for debug.
##############################

if __name__ == "__main__":
    import os
    import sys
    import getopt

    handout_url    = ''
    handout_key    = ''
    chrome_path    = ''

    if ('CHROMEDRIVER_PATH' in os.environ):
        chrome_path = os.environ['CHROMEDRIVER_PATH']
    if ('ROLL20_JOURNAL' in os.environ):
        handout_url = os.environ['ROLL20_JOURNAL']

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hu:k:c:", ["url=", "key=", "chrome="])
    except getopt.GetoptError:
        print('roll20bridge.py -u <Handout URL> -k <Handout Key> -c <ChromeDriver Path>')
        sys.exit(1)
    for opt, arg in opts:
        if opt == "-h":
            print('roll20bridge.py -u <Handout URL> -k <Handout Key> -c <ChromeDriver Path>')
            sys.exit(1)
        elif opt in ("-u", "--url"):
            handout_url = arg
        elif opt in ("-k", "--key"):
            handout_key = arg
        elif opt in ("-c", "--chrome"):
            chrome_path = arg

    #print(handout_url)
    #print(handout_key)
    #print(chrome_path)

    if (handout_url != ''):
        varJSON = load_handout(chrome_path, handout_url, handout_key)
        print("Handout:\n{}".format(json.dumps(varJSON, indent=2, sort_keys=True)))
