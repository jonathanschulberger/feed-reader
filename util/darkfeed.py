import collections
import datetime
import json

import boto3
import requests

from util.feed import FeedReader


class DarkfeedIO_RSS(FeedReader):
    def __init__(self,  config_file_path: str, message_log_file_path: str=None,
                 message_log_depth: int=20):
        # attempt to load s3 configuration from disk
        self.s3_config_file_path = "darkfeed_s3_config.json"

        # initialize the feed object as usual, evaluating any overriden functions like
        #   - load_config
        super().__init__(config_file_path, message_log_file_path, message_log_depth)


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
        request_session = requests.Session()
        headers = collections.OrderedDict()

        headers["Host"] = "darkfeed.io"
        headers["Cookie"] = self.config["cookie"]

        response = request_session.get(self.config["feed_url"], headers=headers)
        response.raise_for_status()

        if 'login1' in response.url:
            print("[ERROR] Darkfeed cookie needs to be refreshed")

        return [{
            "group": entry["attacker_name"],
            "victim": entry["victim_name"],
            "date": datetime.datetime(
                *entry["published_date"][:6], timezone=datetime.timezone.utc),
            "link": entry["link"]
        } for entry in response.entries]
