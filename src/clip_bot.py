import time
import requests
import json
from datetime import datetime, timezone, timedelta

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


# Main loop that polls the streamers one by one and checks for clips in the last hour
while True:

    try:

    # reads streamers.txt
        streamers = getstreamers()

    # opens clips file and loads it for comparison later
        if verbose >= 1:
            print("checking if clips.txt exsists")

        clips_exists = exists("config/clips.txt")

        if clips_exists == True:

            with open("config/clips.txt", 'r') as clipsFile: 
                clips = [line.rstrip() for line in clipsFile]

            if verbose >= 1:
                print(f"content of clips.txt is:\n{clips}")

            with open("config/clips.txt",'w') as clipsFile:
                pass

            if verbose >= 1:
                print("clips.txt read and erased")

        else:
            clips = []
            with open("config/clips.txt",'w') as clipsFile:
                pass

            print("clips.txt did not exsist and was created")

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

        # Continues pulling clips from twitch api
                streamerJson = r.json()
                streamerId = streamerJson["data"][0]["id"]

                if verbose >= 1:
                    print(f"streamer used to poll for clips {streamer} {streamerId}")

                rr=requests.get(f"https://api.twitch.tv/helix/clips?broadcaster_id={streamerId}&started_at={hourAgoFormatted}", headers={'Authorization':f"Bearer {token}", 'Client-Id':twitchClientId})
                clipsJson = rr.json()
                
                if verbose >= 1:
                    print (f"poll response {str(rr)} with json: {json.dumps(clipsJson)}")

        # loop start
                for clip in clipsJson["data"]:

                    clipUrl = clip["url"]

                    if verbose >= 1:
                        print(f"url to post {clipUrl}")

        # checks if clip was allready posted
                    if clipUrl not in clips:

                        rclip = requests.post(webhookurl, data={"content": clipUrl}, params={'wait': 'true'})

                        if "200" in str(rclip):
                            print(f"{clipUrl} posted on discord from {streamer} with response {str(rclip)}")
                        
                        else:
                            print(f"attempted to post {clipUrl} on discord from {streamer} with response {str(rclip)}")
                        
                        if verbose >= 1:
                            print(f"appending {clipUrl} to clips.txt")
                        
                        with open('config/clips.txt', 'a') as clipsFile:
                            clipsFile.write(f"{clipUrl}\n")
                    
                    elif verbose >= 1:
                        print(f"{clipUrl} not posted because it was allready posted")

            except Exception as e:
                print(f"An exception occurred in the main loop whilst checking streamer: {streamer} {str(e)}")

        print("main loop finished, waiting for 1 hour")
        time.sleep(3600)

    except Exception as e:
        print(f"An exception occurred in the main loop: {str(e)} waiting for 1 minute")
        time.sleep(60)