import collections
import datetime
import os
import traceback

import feedparser

from feeds.feed import FeedReader

# constants
BASE_PATH_PREFIX = os.path.dirname(os.path.join(os.path.dirname(__file__)))


class RSS(FeedReader):

    def load_config(self):
        """Sync main feed config from AWS S3"""
        # perform loading of standard config
        super().load_config()

        # update s3 configuration
        self.config["cookie_file_path"] = os.path.join(
            BASE_PATH_PREFIX, self.config["cookie_file_path"])
        with open(self.config["cookie_file_path"], 'r') as cookie_file:
            self.config["cookie"] = cookie_file.read().strip()


    def format_message(self, raw_attributes: dict):
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": self.name.title(),
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Group:*\n{raw_attributes.get('group', None)}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Victim:*\n{raw_attributes.get('victim', None)}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Date:*\n{raw_attributes.get('date', None)}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{raw_attributes.get('link', None)}"
                    }
                }
            ]
        }


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
