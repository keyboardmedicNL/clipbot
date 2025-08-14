import housey_logging
housey_logging.configure()

import time
from datetime import datetime, timezone, timedelta
import config_loader
import requests_error_handler
import twitch_api_handler
import logging
from os.path import exists

config = config_loader.load_config

get_token_from_twitch_api = twitch_api_handler.get_token_from_twitch_api
get_list_of_team_member_uids = twitch_api_handler.get_list_of_team_member_uids

handle_request_error = requests_error_handler.handle_request_error

get_token_from_twitch_api = twitch_api_handler.get_token_from_twitch_api
get_list_of_team_member_uids = twitch_api_handler.get_list_of_team_member_uids
get_list_of_clips = twitch_api_handler.get_list_of_clips
validate_token = twitch_api_handler.validate_token

def get_list_of_streamers(token_from_twitch: str, team_name: str) -> list:

    if team_name == "":

        # gets list of streamers from streamers.txt
        with open("config/streamers.txt", 'r') as file_with_streamer_ids:
            list_of_streamers = [line.rstrip() for line in file_with_streamer_ids]
            if "http" in list_of_streamers[0]:

                get_streamers_trough_request_response = handle_request_error("get",list_of_streamers[0])

                list_of_streamers = get_streamers_trough_request_response.text.splitlines()
                
    else:
        list_of_streamers = get_list_of_team_member_uids(team_name, token_from_twitch)

    logging.info('list of streamers to poll from: %s', list_of_streamers)

    return(list_of_streamers)

# opens clips file and loads it for comparison later or creates it if it does not exsist
def init_clips_file():
        
    clips = []
    logging.debug("checking if clips.txt exsists")

    clips_exists = exists("config/clips.txt")

    if clips_exists:

        with open("config/clips.txt", 'r') as clipsFile: 
            clips = [line.rstrip() for line in clipsFile]

        logging.debug(f"content of clips.txt is:\n{clips}")
        logging.info("clips.txt read and erased")

    else:
        with open("config/clips.txt",'w') as clipsFile:
            pass

        logging.info("clips.txt did not exsist and was created")

    return(clips)

def post_clips_to_discord(list_of_new_clips: list, list_of_clips_to_ignore: list, discord_webhook_url: str) -> list:

    for clip in list_of_new_clips:
        if clip not in list_of_clips_to_ignore:

            send_clip_to_discord_response = handle_request_error(request_type="post",request_url=discord_webhook_url, request_data={"content": clip}, request_params={'wait': 'true'})

            list_of_clips_to_ignore.append(clip)

            logging.info("clip with url: %s was posted to discord webhook with response: %s",clip, send_clip_to_discord_response)

    return(list_of_clips_to_ignore)
         
def save_clips_to_ignore_to_file(list_of_clips_to_ignore: list):
    with open("config/clips.txt",'w') as clips_file:
        pass
    with open("config/clips.txt",'a') as clips_file:
        for clip in list_of_clips_to_ignore:
            clips_file.write(clip + '\n')
    
    logging.info("saved list of previously posted clips to file")

def main():

    loaded_config = config()

    poll_interval_seconds = loaded_config.poll_interval*60

    token = get_token_from_twitch_api()

    list_of_clips_posted_before = init_clips_file()

    while True:

        token = validate_token(token)

        # reads streamers.txt
        streamers = get_list_of_streamers(token, loaded_config.team_name)

        # loop start
        for streamer in streamers:

            # formats day ago timestamp to use for clip request 
            day_ago_timestamp = datetime.now(timezone.utc) - timedelta(hours=24, minutes=00)
            day_ago_formatted_timestamp = day_ago_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")

            logging.debug("current selected streamer: %s", streamer)

            list_of_new_clips = get_list_of_clips(streamer, token, day_ago_formatted_timestamp)   

            list_of_clips_to_save = post_clips_to_discord(list_of_new_clips, list_of_clips_posted_before, loaded_config.discord_webhook_url)

        save_clips_to_ignore_to_file(list_of_clips_to_save)

        logging.info("main loop finished, waiting for %s minutes", loaded_config.poll_interval)
        time.sleep(poll_interval_seconds)

if __name__ == "__main__":
    main()