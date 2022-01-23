import time
import traceback

from feeds.darkfeed import DarkfeedIO_RSS


# constants
QUERY_DELAY = 60  # 60 second delay between reading from APIs
REPORT_OUTAGE_IN_SLACK = True  # post online/offline message to feed-specific slack


def main():
    ################################ DEFINE FEEDS HERE #################################
    ################ <feed-name>: { "feed": <initialized-feed-object> } ################
    feeds = {
        "Darkfeed": { "feed": DarkfeedIO_RSS("darkfeed_config.json") },
    }
    ####################################################################################

    print('[INFO] feeds initialized successfully')

    while True:
        start_time = time.time()
        try:
            # process feeds
            for feed_name, feed in feeds.items():
                try:
                    feed["feed"].check_feed()

                    # report to slack if feed went from offline to online
                    if REPORT_OUTAGE_IN_SLACK and not feed.get("last_query_succeeded"):
                        feed["feed"].send_slack_message(f"{feed_name} is back online")
                    feed["last_query_succeeded"] = True
                except Exception:
                    print(f"[ERROR] could not process '{feed_name}'\n{traceback.format_exc()}")

                    # report to slack if feed went from online to offline
                    if REPORT_OUTAGE_IN_SLACK and feed.get("last_query_succeeded"):
                        feed["feed"].send_slack_message(f"{feed_name.title()} is offline")
                    feed["last_query_succeeded"] = False

        except Exception:
            print(f"[ERROR] unexpected error in main thread\n{traceback.format_exc()}")
        
        # always enforce sleep in between requests
        time_left = QUERY_DELAY - (time.time() - start_time)
        if time_left > 0:
            time.sleep(time_left)


if __name__ == "__main__":
    main()
