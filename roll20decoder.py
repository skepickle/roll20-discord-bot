from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import re
import time

class Roll20Decoder:

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
    def decode_roll20_journal(cls,chrome,journal,key):

        #Define webdriver with path
        options = Options()
        options.headless = True
        driver = webdriver.Chrome(executable_path=chrome, chrome_options=options)

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
