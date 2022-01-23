import collections
import datetime
import json
import os
import traceback

import boto3
import feedparser

from feeds.feed import FeedReader


class DarkfeedIO_RSS(FeedReader):
    def __init__(self,  config_file_name: str, message_log_file_path: str=None,
                 message_log_depth: int=20):
        # attempt to load s3 configuration from disk
        self.s3_config_file_path = os.path.join("config", f"s3_{config_file_name}")

        # initialize the feed object as usual, evaluating any overriden functions like
        #   - load_config
        super().__init__(config_file_name, message_log_file_path, message_log_depth)


    def load_config(self):
        """Sync main feed config from AWS S3"""
        # update s3 configuration
        with open(self.s3_config_file_path, 'r') as config_file:
            self.s3_config = json.load(config_file)

        # sync remote config with new local config values
        self.sync_config_from_s3()

        # perform loading of standard config
        super().load_config()


    def sync_config_from_s3(self):
        """Use S3 config to sync main feed config from AWS S3 bucket"""
        s3 = boto3.client(
            's3', aws_access_key_id=self.s3_config["aws_access_key_id"],
            aws_secret_access_key=self.s3_config["aws_secret_access_key"])
        s3.download_file(
            self.s3_config["s3_bucket"], self.s3_config["s3_filename"], self.config_file_path)


    def retrieve_feed_content(self):
        """Read and convert raw feed content into a list of dictionaries"""
        headers = collections.OrderedDict()

        headers["Host"] = "darkfeed.io"
        headers["Cookie"] = self.config["cookie"]

        response = feedparser.parse(self.config["feed_url"], request_headers=headers)
        
        # verify expected response was received
        if response.get('status') not in [200, 201] or not isinstance(response.get('entries'), list):
            raise RuntimeError(
                f"[ERROR] unexpected error while reading feed\n{traceback.format_exc()}")

        if 'login1' in response.url:
            print("[ERROR] Darkfeed cookie needs to be refreshed")

        return [{
            "group": entry["title"],
            "victim": entry["summary"],
            "date": str(datetime.datetime(*entry["published_parsed"][:6],
                                          tzinfo=datetime.timezone.utc)),
            "link": entry["link"]
        } for entry in response.entries]
