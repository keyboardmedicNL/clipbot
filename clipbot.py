import time
import requests
import json
from datetime import datetime, timezone, timedelta
import threading
from subprocess import call
from os.path import exists

# formats embed for discord webhook and posts to url
def discord_embed(title,color,description,ping):
    if webhooklogurl != "":
        if color == "blue":
            color = 1523940
        elif color == "yellow":
            color = 14081792
        elif color == "red":
            color = 10159108
        elif color == "green":
            color = 703235
        elif color == "purple":
            color = 10622948
        elif color == "gray" or color == "grey":
            color = 1776669
        if ping:
            ping_string = f"<@{ping_id}>"
        else:
            ping_string = ""
        data_for_log_hook = {"content": ping_string, "embeds": [
                {
                    "title": title,
                    "color": color,
                    "description": description
                }
            ]}
        rl = requests.post(webhooklogurl, json=data_for_log_hook, params={'wait': 'true'})
        if verbose >= 2:
            print(f"sending message to discord remote log webhook with title: {title} Color: {color} Description: {description} and ping: {ping_string} . Discord response is {str(rl)}")
        time.sleep(1)

# formats notification for use with gotify
def gotify(title,message,priority):
    if gotifyurl != "":
        gr = requests.post(gotifyurl, data={"title": title, "message": message, "priority":priority})
        if verbose >= 2:
            print(f"sending notification to gotify with title: {title} message: {message} priority: {priority}")
        time.sleep(1)

# gets new auth token from twitch
def gettoken():
    print("Requesting new auth token from twitch")
    discord_embed("Clipbot","yellow","Requesting new auth token from twitch",False)
    rrr=requests.post("https://id.twitch.tv/oauth2/token", data={"client_id" : str(twitchClientId), "client_secret" : str(twitchSecret), "grant_type":"client_credentials"})
    tokenJson = rrr.json()
    token = tokenJson["access_token"]
    if verbose >= 1:
        print(f"new twitch auth token is: {token}")
        discord_embed("Clipbot","yellow","New twitch auth token recieved",False)
    with open(r'config/token.txt', 'w') as tokenFile:
        tokenFile.write("%s\n" % token)
        tokenFile.close()
    return(token)

# gets list of streamers to poll
def getstreamers():
    with open("config/streamers.txt", 'r') as streamerfile:
        streamers = [line.rstrip() for line in streamerfile]
        if "http" in streamers[0]:
            if verbose >= 1:
                print(f"found {str(streamers[0])} in streamers.txt and will follow it to get list of streamers")
                discord_embed("Clipbot","yellow",f"found {str(streamers[0])} in streamers.txt and will follow it to get list of streamers",False)
            response = requests.get(streamers[0])
            streamers = response.text.splitlines()
        if verbose >= 1:
            print(f"list of streamers to poll:\n{streamers}")
            discord_embed("Clipbot",14081792,f"list of streamers to poll:\n{streamers}",False)
    return(streamers)

# Loads variables used in script
with open("config/config.json") as config:
    configJson = json.load(config)
    twitchClientId = configJson["twitchClientId"]
    twitchSecret = configJson["twitchSecret"]
    webhookurl = configJson["webhookurl"]
    webhooklogurl = configJson["webhooklogurl"]
    webhookmonitorurl = configJson["webhookmonitorurl"]
    webport = configJson["webport"]
    gotifyurl = configJson["gotifyurl"]
    ping_id = configJson["pingid"]
    verbose = int(configJson["verbose"])
print("succesfully loaded config")
discord_embed("Clipbot",14081792,"succesfully loaded config",False)

#webserver for monitoring purposes
if webport != "":
    def thread_second(): # start webserver.py as a second threat to allow it to run parallel with main script
        call(["python", "webserver.py"])
    processThread = threading.Thread(target=thread_second)
    processThread.start()
    print("starting webserver for local monitoring") 
    discord_embed("Clipbot","purple","starting webserver for local monitoring",False)

#post process to talk to remote monitor
if webhookmonitorurl != "":
    def thread_third(): # start post.py as a third threat to allow it to run parallel with main script
        call(["python", "post.py"])
    processThread = threading.Thread(target=thread_third)
    processThread.start()
    print("starting post server for remote monitoring")
    discord_embed("Clipbot","purple","starting post server for remote monitoring",False)

#opens file to get auth token
token_exists = exists("config/token.txt")
if token_exists == True:
    with open("config/token.txt", 'r') as file2:
        tokenRaw = str(file2.readline())
        token = tokenRaw.strip()
        file2.close()
    print ("Twitch auth oken to use for auth: " + token)
    discord_embed("Clipbot","yellow","Twitch auth token loaded succesfully",False)
else:
    token = gettoken()

# Main loop that polls the streamers one by one and checks for clips in the last hour
while True:
    try:
    # reads streamers.txt
        streamers = getstreamers()
    # opens clips file and loads it for comparison later
        if verbose >= 1:
            print("checking if clips.txt exsists")
            discord_embed("Clipbot","blue","checking if clips.txt exsists",False)
        clips_exists = exists("config/clips.txt")
        if clips_exists == True:
            with open("config/clips.txt", 'r') as clipsFile: 
                clips = [line.rstrip() for line in clipsFile]
            if verbose >= 1:
                print(f"content of clips.txt is:\n{clips}")
                discord_embed("Clipbot","blue",f"content of clips.txt is:\n{clips}",False)
            with open("config/clips.txt",'w') as clipsFile:
                pass
            if verbose >= 1:
                print("clips.txt read and erased")
                discord_embed("Clipbot","blue","clips.txt read and erased",False)
        else:
            clips = []
            with open("config/clips.txt",'w') as clipsFile:
                pass
            print("clips.txt did not exsist and was created")
            discord_embed("Clipbot","blue","clips.txt did not exsist and was created",False)    
    # Gets current time and hour ago in utc for use in request
        currentTime = (datetime.now(timezone.utc))
        currentTimeFormatted = (currentTime.strftime("%Y-%m-%dT%H:%M:%SZ"))
        hourAgo = datetime.now(timezone.utc) - timedelta(hours=1, minutes=00)
        hourAgoFormatted = hourAgo.strftime("%Y-%m-%dT%H:%M:%SZ")
    # loop start
        for streamer in streamers:
            try:
                r=requests.get(f"https://api.twitch.tv/helix/users?login={streamer}", headers={'Authorization':f"Bearer {token}", 'Client-Id':twitchClientId})
                print(f"Request response: {r}")
        # checks if token is valid and requests a new one if not
                if "401" in str(r):
                    token = gettoken()
                    r=requests.get(f"https://api.twitch.tv/helix/users?login={streamer}", headers={'Authorization':f"Bearer {token}", 'Client-Id':twitchClientId})
                elif "200" in str(r):
                    if verbose >= 1:
                        print(f"twitch auth token: {token} is valid and will be used")
                else:
                    discord_embed("Clipbot","yellow",f"request response: {r}",False)
        # Continues pulling clips from twitch api
                streamerJson = r.json()
                streamerId = streamerJson["data"][0]["id"]
                if verbose >= 1:
                    print(f"streamer used to poll for clips {streamer} {streamerId}")
                    discord_embed("Clipbot","yellow",f"streamer used to poll for clips {streamer} {streamerId}",False)
                rr=requests.get(f"https://api.twitch.tv/helix/clips?broadcaster_id={streamerId}&started_at={hourAgoFormatted}", headers={'Authorization':f"Bearer {token}", 'Client-Id':twitchClientId})
                clipsJson = rr.json()
                if verbose >= 1:
                    print (f"poll response {str(rr)} with json: {json.dumps(clipsJson)}")
                    discord_embed("Clipbot","yellow",f"poll response {str(rr)} with json: {json.dumps(clipsJson)}",False)
        # loop start
                for clip in clipsJson["data"]:
                    clipUrl = clip["url"]
                    if verbose >= 1:
                        print(f"url to post {clipUrl}")
                        discord_embed("Clipbot","yellow",f"url to post {clipUrl}",False)
        # checks if clip was allready posted
                    if clipUrl not in clips:
                        r = requests.post(webhookurl, data={"content": clipUrl}, params={'wait': 'true'})
                        if 200 in str(r):
                            print(f"{clipUrl} posted on discord from {streamer} with response {str(r)}")
                            discord_embed("Clipbot","green",f"{clipUrl} posted on discord from {streamer} with response {str(r)}",False)
                        else:
                            print(f"attempted to post {clipUrl} on discord from {streamer} with response {str(r)}")
                            discord_embed("Clipbot","red",f"attempted to post {clipUrl} on discord from {streamer} with response {str(r)}",True)
                            gotify("Clipbot",f"attempted to post {clipUrl} on discord from {streamer} with response {str(r)}","5")
                        if verbose >= 1:
                            print(f"appending {clipUrl} to clips.txt")
                            discord_embed("Clipbot","blue",f"appending {clipUrl} to clips.txt",False)
                        with open('config/clips.txt', 'a') as clipsFile:
                            clipsFile.write(f"{clipUrl}\n")
                    elif verbose >= 1:
                        print(f"{clipUrl} not posted because it was allready posted")
                        discord_embed("Clipbot","green",f"{clipUrl} not posted because it was allready posted",False)
            except Exception as e:
                print(f"An exception occurred in the main loop whilst checking streamer: {streamer} {str(e)}")
                discord_embed("Clipbot","red",f"An exception occurred in the main loop whilst checking streamer: {streamer} {str(e)}",True)
                gotify("Clipbot",f"An exception occurred in the main loop whilst checking streamer: {streamer} {str(e)}","5")
        print("main loop finished, waiting for 1 hour")
        discord_embed("Clipbot","gray","main loop finished, waiting for 1 hour",False)
        time.sleep(3600)
    except Exception as e:
        print(f"An exception occurred in the main loop: {str(e)} waiting for 1 minute")
        discord_embed("Clipbot","red",f"An exception occurred in the main loop: {str(e)} waiting for 1 minute",True)
        gotify("Clipbot",f"An exception occurred in the main loop: {str(e)} waiting for 1 minute","5")
        time.sleep(60)