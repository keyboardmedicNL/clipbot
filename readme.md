# what does it do
A simple bot that polls twitch for clips from a predefined list of streamers over the last hour and posts new clips to a discord webhook

included are:
- a post script that sends a http post to a watchdog server of your choosing, wich wont happen if the url is left blank in the config
- a http webserver running to use for uptime monitoring by having an approachable url wich can be checked with something like uptime kuma
- remote logging capabilities with use of a discord webhook where debugging messages get posted, wich wont happen if the url is left blank in the config

# how to use:
1. place all contents in a folder and make a "config" folder.
2. make a config.json and copy the text below into the file 
```
{
    "twitchClientId": "TWITCH_API_CLIENT_ID",
    "twitchSecret": "TWITCH_API_SECRET",
    "webhookurl": "MAIN_WEBHOOK_WHERE_CLIPS_GET_POSTED",
    "webhooklogurl": "WEBHOOK_TO_USE_TO_LOG_DEBUGGING_MESSAGES_TO_A_WEBHOOK/OPTIONAL",
    "webhookmonitorurl": "URL_FOR_REMOTE_MONITORING_SERVER/OPTIONAL",
    "botname": "NAME_VALUE_SEND_TO_REMOTE_MONITORING_SERVER/OPTIONAL",
    "posttimeout": "TIME_BETWEEN_POSTS_TO_REMOTE_MONITORING/OPTIONAL",
    "hostname": "ADRESS_FOR_LOCAL_WEBSERVER",
    "webport": PORT_FOR_LOCAL_WEBSERVER
}
```
3. create a streamers.txt file in the config folder and add every streamer you want to poll on a new line, alternativly add the url to a txt file that contains the list to poll
4. input the correct data and launch the script clipbot.py
* leave optional entries blank if you do not intent to use them but do include them otherwise the script will throw an error


Optionally a dockerfile is included wich can be used to build a docker image or use the one on my repository with the following code

```
docker run -dit --name clipbot -v /path/to/config:/usr/src/app/config -p <port for webserver>:<port defined in config> keyboardmedic/clipbot:latest
```