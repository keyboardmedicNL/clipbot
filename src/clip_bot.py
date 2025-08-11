import housey_logging
housey_logging.configure()

import time
import requests
from datetime import datetime, timezone, timedelta
import config_loader
import requests_error_handler
import twitch_api_handler
import logging
from os.path import exists

config = config_loader.load_config

get_token_from_twitch_api = twitch_api_handler.get_token_from_twitch_api
get_list_of_team_member_uids = twitch_api_handler.get_list_of_team_member_uids

init_error_handler = requests_error_handler.init_error_handler
handle_response_not_ok = requests_error_handler.handle_response_not_ok
handle_request_exception = requests_error_handler.handle_request_exception
raise_no_more_tries_exception = requests_error_handler.raise_no_more_tries_exception

get_token_from_twitch_api = twitch_api_handler.get_token_from_twitch_api
get_list_of_team_member_uids = twitch_api_handler.get_list_of_team_member_uids
get_list_of_clips = twitch_api_handler.get_list_of_clips


def get_list_of_streamers(token_from_twitch: str, team_name: str) -> list:

    if team_name == "":

        # gets list of streamers from streamers.txt
        with open("config/streamers.txt", 'r') as file_with_streamer_ids:
            list_of_streamers = [line.rstrip() for line in file_with_streamer_ids]
            if "http" in list_of_streamers[0]:

                time_before_retry, max_errors_allowed, error_count = init_error_handler()

                while error_count < max_errors_allowed:

                    try:
                        get_streamers_trough_request_response = requests.get(list_of_streamers[0])

                        if get_streamers_trough_request_response.ok:
                            list_of_streamers = get_streamers_trough_request_response.text.splitlines()
                            break

                        else:
                            error_count, remaining_errors = handle_response_not_ok(error_count)
                            logging.error('was unable to get list of streamers trough request with response: %s with exception: %s trying %s more times and waiting for %s seconds', get_streamers_trough_request_response, remaining_errors, time_before_retry)
                            if error_count != max_errors_allowed:
                                time.sleep(time_before_retry)

                    except Exception as e:
                        error_count, remaining_errors = handle_request_exception(error_count)
                        logging.error('was unable to get list of streamers trough request with exception: %s trying %s more times and waiting for %s seconds', e, remaining_errors, time_before_retry)
                        if error_count != max_errors_allowed:
                            time.sleep(time_before_retry)

                if error_count == max_errors_allowed:
                    raise_no_more_tries_exception(max_errors_allowed)
                
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

            time_before_retry, max_errors_allowed, error_count = init_error_handler()

            while error_count < max_errors_allowed:

                try:
                    send_clip_to_discord_response = requests.post(discord_webhook_url, data={"content": clip}, params={'wait': 'true'})

                    list_of_clips_to_ignore.append(clip)

                    if send_clip_to_discord_response.ok:
                        logging.info("clip with url: %s was posted to discord webhook with response: %s",clip, send_clip_to_discord_response)
                        break

                    else:
                        error_count, remaining_errors = handle_response_not_ok(error_count)
                        logging.error("unable to post clip with url: %s to discord with response: %s trying %s more times and waiting for %s seconds",clip, send_clip_to_discord_response, remaining_errors , time_before_retry)
                        if error_count != max_errors_allowed:
                            time.sleep(time_before_retry)
                
                except Exception as e:
                    error_count, remaining_errors = handle_request_exception(error_count)
                    logging.error("unable to post clip to discord with exception: %s trying %s more times and waiting for %s seconds", e, remaining_errors, time_before_retry)
                    if error_count != max_errors_allowed:
                        time.sleep(time_before_retry)

            if error_count == max_errors_allowed:
                raise_no_more_tries_exception(max_errors_allowed)
    
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