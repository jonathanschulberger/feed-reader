import collections
import json
import os
import traceback

import requests

# constants
BASE_PATH_PREFIX = os.path.dirname(os.path.join(os.path.dirname(__file__)))
CONFIG_PATH_PREFIX = os.path.join(BASE_PATH_PREFIX, "config")
LOG_PATH_PREFIX = os.path.join(BASE_PATH_PREFIX, "logs")


class FeedReader:
    def __init__(self, feed_name: str, message_log_file_path: str=None,
                 message_log_depth: int=20):
        self.name = feed_name
        self.message_log_depth = 20
        self.last_query_succeeded = True

        # load config from disk
        # "feed_url" and "slack_hook_url" must be included
        self.config_file_path = os.path.join(CONFIG_PATH_PREFIX, f"{feed_name}.json")
        self.load_config()

        self.message_log_file_path = message_log_file_path or \
                                     os.path.join(LOG_PATH_PREFIX, f"{feed_name}.json")

        # load log history from disk
        self.load_messages_from_disk()


    def load_config(self):
        with open(self.config_file_path, 'r') as config_file:
            self.config = json.load(config_file)


    def retrieve_feed_content(self):
        """Read and convert raw feed content into key/value pairs"""
        raise RuntimeError("NOT IMPLEMENTED")


    def format_message(self, raw_attributes: dict):
        """Convert key/value pairs into a json-capable string"""
        attributes = {
            "Group": raw_attributes.get("group", None),
            "Victim": raw_attributes.get("victim,", None),
            "Date": raw_attributes.get("date", None),
            "Link": raw_attributes.get("link", None)
        }

        for key, value in raw_attributes.items():
            if key not in attributes:
                attributes[key.replace("_", " ").title()] = value

        return "\n".join((f"{key}: {value}" for key, value in attributes.items()))


    def check_feed(self):
        # refresh config
        self.load_config()

        # load feed using most recent config values
        self.process_feed_content(self.retrieve_feed_content())


    def process_feed_content(self, feed_content: list):
        if not feed_content:
            print("[WARNING] no feed content to process")
            return

        # feed content is [<newest>, ... , <oldest>]
        # find index of oldest new entry
        oldest_new_entry_idx = None
        for idx, raw_message in enumerate(feed_content):
            if raw_message in self.message_log:
                # don't bother checking older messages 
                break
            oldest_new_entry_idx = idx

        # stop if there are no new entries
        if oldest_new_entry_idx is None:
            return

        while oldest_new_entry_idx >= 0:
            raw_message = feed_content[oldest_new_entry_idx]
            self.send_slack_message(self.format_message(raw_message))
            self.message_log.appendleft(raw_message)
            oldest_new_entry_idx -= 1

        # flush message log to disk
        self.save_messages_to_disk()


    def send_slack_message(self, message):
        request_headers = {
            "Content-type": "application/json"
        }

        # directly support rich slack message formats
        data = message

        # fall back to base message format if only a string is supplied
        if isinstance(message, str):
            data = {
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": message
                        }
                    },
                    {
                        "type": "divider"
                    }
                ]
            }

        # post message to slack
        response = requests.post(
            self.config["slack_hook_url"], headers=request_headers,
            data=json.dumps(data))

        # verify slack responded appropriately
        response.raise_for_status()


    def load_messages_from_disk(self):
        try:     
            # load log from disk
            if os.path.exists(self.message_log_file_path):
                with open(self.message_log_file_path, 'r') as on_disk_log:
                    self.message_log = collections.deque(
                       json.load(on_disk_log), self.message_log_depth 
                    )
        except Exception:
            print(f"[WARNING] could not load message log from disk\n{traceback.format_exc()}")


    def save_messages_to_disk(self):
        try:
            with open(self.message_log_file_path, 'w') as on_disk_log:
                json.dump([message for message in self.message_log if message], on_disk_log)
        except Exception:
            print(f"[WARNING] could not write to message log on disk\n{traceback.format_exc()}")
