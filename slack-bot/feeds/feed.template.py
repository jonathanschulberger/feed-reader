from feeds.feed import FeedReader


class SiteName(FeedReader):
    def retrieve_feed_content(self):
        """Read and convert raw feed content into a list of dictionaries"""
        # cookie = <load cookie from file>
        # request_session = requests.Session()
        # headers = collections.OrderedDict()

        # headers["Host"] = <host>
        # headers["Cookie"] = <cookie>

        # response = request_session.get(self.feed_url, headers=headers)
        # return [<formatted-entry> for entry in response.entries]
        super().retrieve_feed_content()


    def format_message(raw_attributes: dict):
        """
            Convert key/value pairs into a json-compatible string
              - This can be overridden if the formatting is more complex
        """
        super().format_message()
