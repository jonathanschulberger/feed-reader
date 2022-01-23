import collections
import hashlib
import json
import os
import traceback

import requests


class FeedReader:
    def __init__(self, config_file_path: str, message_log_file_path: str=None,
                 message_log_depth: int=20):
        # load config from disk
        # "feed_url" and "slack_hook_url" must be included
        self.config_file_path = config_file_path
        self.load_config()

        self.message_log_file_path = message_log_file_path or \
                                     hashlib.md5(self.config["feed_url"].encode()).hexdigest() + ".json"
        self.message_log = collections.deque(message_log_depth * [None], message_log_depth)

        # load log history from disk
        self.load_messages_from_disk()


    def load_config(self):
        with open(self.config_file_path, 'r') as config_file:
            self.config = json.load(config_file)


    def retrieve_feed_content(self):
        """Read and convert raw feed content into key/value pairs"""
        raise RuntimeError("NOT IMPLEMENTED")


    def format_message(raw_attributes: dict):
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

        # assume feed content is [<newest>, ... , <oldest>]
        # process in order or [<oldest>, ... , <newest>]
        for idx, raw_message in enumerate(self.retrieve_feed_content().reverse()):
            try:
                message = self.format_message(raw_message)
            
                if message in self.message_log:
                    # go to next iteration, might still be a new message
                    if idx:
                        continue

                    # is this the exact same list of messages?
                    if self.message_log.index(message) == len(self.message_log) - 1:
                        return

                # new message found
                self.send_slack_message(message)
                self.message_log.appendleft(message)
            except Exception:
                print(f"[ERROR] could not parse message from\n{raw_message}")
                break

        # flush message log to disk
        self.save_messages_to_disk()


    def send_slack_message(self, message: str):
        request_headers = {
            "Content-type": "application/json"
        }

        # post message to slack
        response = requests.post(
            self.config["slack_hook_url"], headers=request_headers,
            data=json.dumps({"text": message}))

        # verify slack responded appropriately
        response.raise_for_status()


    def load_messages_from_disk(self):
        try:
            # clear current log
            log_depth = len(self.message_log)
            self.message_log = collections.deque(log_depth * [None], log_depth)
            
            # load log from disk
            if os.path.exists(self.message_log_file_path):
                with open(self.message_log_file_path, 'r') as on_disk_log:
                    for message in json.load(on_disk_log).reverse():
                        self.message_log.appendleft(message)
        except Exception:
            print(f"[WARNING] could not load message log from disk\n{traceback.format_exc()}")


    def save_messages_to_disk(self):
        try:
            with open(self.message_log_file_path, 'w') as on_disk_log:
                json.dump([message for message in self.message_log if message], on_disk_log)
        except Exception:
            print(f"[WARNING] could not write to message log on disk\n{traceback.format_exc()}")
