import time
import requests
import json
from datetime import datetime, timezone, timedelta
import threading
from subprocess import call
from os.path import exists

configfile=False
channelsfile=False
webservercheck=False
postcheck=False
tokenCheck=False

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

# Loads variables used in script
while configfile == False:
    try:
        with open("config/config.json") as config:
            configJson = json.load(config)
            twitchClientId = configJson["twitchClientId"]
            twitchSecret = configJson["twitchSecret"]
            webhookurl = configJson["webhookurl"]
            webhooklogurl = configJson["webhooklogurl"]
            webhookmonitorurl = configJson["webhookmonitorurl"]
            streamers = configJson["streamers"]
            config.close()
        configfile = True # stops loop when loaded succesfully
        print("<CLIPBOT> succesfully loaded config")
        discord_embed("Clipbot",14081792,"succesfully loaded config")
    except Exception as e: 
        print(f"An exception occurred whilst trying to read the config: {str(e)} waiting for 1 minute")
        time.sleep(60)

#webserver for monitoring purposes
while webservercheck == False: # loop to ensure webserver gets loaded
    try:
        file_exists = exists("webserver.py")
        if file_exists == True: # check added so exception actually triggers
            def thread_second(): # start webserver.py as a second threat to allow it to run parallel with main script
                call(["python", "webserver.py"])
            processThread = threading.Thread(target=thread_second)
            processThread.start()
            webservercheck = True # stops loop if succesfull
            print("<CLIPBOT> starting webserver for local monitoring") 
            discord_embed("Clipbot",14081792,"starting webserver for local monitoring")
    except Exception as e: 
        print(f"An exception occurred whilst trying to start the webserver: {str(e)} waiting for 1 minute")
        discord_embed("Clipbot",10159108,f"An exception occurred whilst trying to start the webserver: {str(e)} waiting for 1 minute")
        time.sleep(60)

#post process to talk to remote monitor
while postcheck == False: # loop to ensure post gets loaded
    try:
        file_exists = exists("post.py")
        if file_exists == True: # check added so exception actually triggers
            if webhookmonitorurl != "":
                def thread_third(): # start post.py as a third threat to allow it to run parallel with main script
                    call(["python", "post.py"])
                processThread = threading.Thread(target=thread_third)
                processThread.start()
                postcheck = True # stops loop if succesfull
                print("<CLIPBOT> starting post server for remote monitoring")
                discord_embed("Clipbot",14081792,"starting post server for remote monitoring")
    except Exception as e: # catches exception
        print(f"An exception occurred whilst trying to start the post server: {str(e)} waiting for 1 minute")
        discord_embed("Clipbot",10159108,f"An exception occurred whilst trying to start the post server: {str(e)} waiting for 1 minute")
        time.sleep(60)

#opens file to get auth token
while tokenCheck == False:
    try:
        with open("config/token.txt", 'r') as file2:
            tokenRaw = str(file2.readline())
            token = tokenRaw.strip()
            file2.close()
        tokenCheck = True
        print ("Token to use for auth: " + token)
        discord_embed("Clipbot",14081792,"auth token loaded succesfully")
    except Exception as e:
        print(f"An exception occurred whilst trying to read the tokenfile: {str(e)} waiting for 1 minute")
        discord_embed("Clipbot",10159108,f"An exception occurred whilst trying to read the tokenfile: {str(e)} waiting for 1 minute")
        time.sleep(60)

# Main loop that polls the streamers one by one and checks for clips in the last hour
while True:
    try:
    # opens clips file and loads it for comparison later
        with open("config/clips.txt", 'r') as clipsFile: 
            clips = [line.rstrip() for line in clipsFile]
            clipsFile.close()
        with open("config/clips.txt",'w') as clipsFile:
            pass
    # Gets current time and hour ago in utc for use in request
        currentTime = (datetime.now(timezone.utc))
        currentTimeFormatted = (currentTime.strftime("%Y-%m-%dT%H:%M:%SZ"))
        hourAgo = datetime.now(timezone.utc) - timedelta(hours=1, minutes=00)
        hourAgoFormatted = hourAgo.strftime("%Y-%m-%dT%H:%M:%SZ")
    # loop start
        for streamer in streamers:
            r=requests.get(f"https://api.twitch.tv/helix/users?login={streamer}", headers={'Authorization':f"Bearer {token}", 'Client-Id':twitchClientId})
            print(f"Request response: {r}")
    # checks if token is valid and requests a new one if not
            if "401" in str(r):
                print("Requesting new token from twitch")
                discord_embed("Clipbot",14081792,"Requesting new token from twitch")
                rrr=requests.post("https://id.twitch.tv/oauth2/token", data={"client_id" : str(twitchClientId), "client_secret" : str(twitchSecret), "grant_type":"client_credentials"})
                tokenJson = rrr.json()
                token = tokenJson["access_token"]
                print(f"new token is: {token}")
                with open(r'config/token.txt', 'w') as tokenFile:
                    tokenFile.write("%s\n" % token)
                    tokenFile.close()
                r=requests.get(f"https://api.twitch.tv/helix/users?login={streamer}", headers={'Authorization':f"Bearer {token}", 'Client-Id':twitchClientId})
            elif "200" in str(r):
                print(f"{token} is valid and will be used")
            else:
                discord_embed("Clipbot",10159108,f"request response: {r}")
    # Continues pulling clips from twitch api
            streamerJson = r.json()
            streamerId = streamerJson["data"][0]["id"]
            print(f"<CLIPBOT> streamer used to poll for clips {streamer} {streamerId}")
            discord_embed("Clipbot",14081792,f"streamer used to poll for clips {streamer} {streamerId}")
            rr=requests.get(f"https://api.twitch.tv/helix/clips?broadcaster_id={streamerId}&started_at={hourAgoFormatted}", headers={'Authorization':f"Bearer {token}", 'Client-Id':twitchClientId})
            clipsJson = rr.json()
            print (f"json recieved from poll: {json.dumps(clipsJson)}")
    # loop start
            for clip in clipsJson["data"]:
                clipUrl = clip["url"]
                print(f"url to post {clipUrl}")
    # checks if clip was allready posted
                if clipUrl not in clips:
                    r = requests.post(webhookurl, data={"content": clipUrl})
                    print(f"{clipUrl} posted on discord")
                    discord_embed("Clipbot",703235,f"{clipUrl} posted on discord")
                    with open('config/clips.txt', 'a') as clipsFile:
                        clipsFile.write(clipUrl + '\n')
                        clipsFile.close()
                else:
                    print(f"{clipUrl} not posted because it was allready posted")
                    discord_embed("Clipbot",14081792,f"{clipUrl} not posted because it was allready posted")
        print("waiting for 1 hour")
        discord_embed("Clipbot",14081792,"waiting for 1 hour")
        time.sleep(3600)
    except Exception as e:
        print(f"An exception occurred in the main loop: {str(e)} waiting for 1 minute")
        discord_embed("Clipbot",10159108,f"An exception occurred in the main loop: {str(e)} waiting for 1 minute")
        time.sleep(60)