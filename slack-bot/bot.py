import time
import traceback

from datetime import datetime, timezone

from feeds import darkfeed


# constants
QUERY_DELAY = 60  # 60 second delay between reading from APIs
REPORT_OUTAGE_IN_SLACK = True  # post online/offline message to feed-specific slack
SYSLOG_DATE_FORMAT = r'%B %d %Y, %H:%M:%S.%f%z (%Z)'


def main():
    ################################ DEFINE FEEDS HERE #################################
    ################ <feed-name>: { "feed": <initialized-feed-object> } ################
    feeds = [
        darkfeed.RSS("darkfeed")
    ]
    ####################################################################################

    print('[INFO] feeds initialized successfully')

    while True:
        start_time = time.time()
        try:
            # process feeds
            for feed in feeds:
                try:
                    feed.check_feed()

                    # report to slack if feed went from offline to online
                    if REPORT_OUTAGE_IN_SLACK and not feed.last_query_succeeded:
                        feed.send_slack_message(f"{feed.name.title()} is back online")
                    feed.last_query_succeeded = True
                except Exception:
                    print(f"[ERROR] could not process '{feed.name}'\n{traceback.format_exc()}")

                    # report to slack if feed went from online to offline
                    if REPORT_OUTAGE_IN_SLACK and feed.last_query_succeeded:
                        feed.send_slack_message(f"{feed.name.title()} is offline")
                    feed.last_query_succeeded = False

        except Exception:
            print(f"[ERROR] unexpected error in main thread\n{traceback.format_exc()}")
        
        # always enforce sleep in between requests
        print("[INFO] cycle completed "
              f"{datetime.utcnow().replace(tzinfo=timezone.utc).strftime(SYSLOG_DATE_FORMAT)} "
              f"({time.time() - start_time:.2f} seconds)")
        time_left = QUERY_DELAY - (time.time() - start_time)
        if time_left > 0:
            time.sleep(time_left)


if __name__ == "__main__":
    main()
