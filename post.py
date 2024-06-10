# imports needed libraries
import requests
import time
import json
from datetime import datetime, timezone, timedelta

# formats embed for discord webhook and posts to url
def discord_embed(title,color,description):
    if webhooklogurl != "":
        data = {"embeds": [
                {
                    "title": title,
                    "color": color,
                    "description": description
                }
            ]}
        rl = requests.post(webhooklogurl, json=data)

# loads needed data from config to variables
with open("config/config.json") as config: # opens config and stores data in variables
    configJson = json.load(config)
    webhookmonitorurl = configJson["webhookmonitorurl"]
    botname = configJson["botname"]
    timeout = 60*int(configJson["posttimeout"])
    webhooklogurl = configJson["webhooklogurl"]
    config.close()
    print("<POST> Succesfully loaded config")
    discord_embed("Clipbot/post",14081792,"succesfully loaded config")

# main loop
while True:
    currentTime = (datetime.now(timezone.utc))
    currentTime = currentTime.timestamp()
    myobj = {'name': botname, 'time': currentTime} # formats currenttime in unix timestamp and botname into correct json formatting
    try:
        x = requests.post( webhookmonitorurl, json = myobj) # sends post request
        print("<POST> webhook response is: " + x.text) # log message
        discord_embed("Clipbot/post",14081792,f"post send to webhook with response: {x.text}")
    except Exception as e: # catches exception
        print(f"<POST> An exception occurred in main loop: {str(e)}")
        discord_embed("Clipbot/post",10159108,f"An exception occurred in main loop: {str(e)}")
    time.sleep(timeout)