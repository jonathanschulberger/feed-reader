# feed-reader
Translate any type of feed into slack messages


## Define Feeds

- Feed definitions are declared (here)[]

- Other feed types can be created by modifying feeds/feed.template.py

- Darkfeed RSS Workflow:
  1) pull config using S3 credentials
  2) use config for querying feed
  3) push updates to slack
  4) sleep for 60 seconds
  5) repeat


## Feed Config Rules

1) Config must be placed at config/<config-file-name>
2) <config-file-name> is typically <feed-name>_config.json
3) Config must be json with the root object being an associative array
4) Config must include the following key/value pairs:
 - feed_url: str -> The URL of the feed
 - slack_webhook_url: str -> The generated webhook URL used for dispatching messages

See config/<feed-name>_config.json.template for a more visual example.


## Darkfeed Config Rules

[Standard Config]
1) Feed definition in bot.py must be initialized with filename in S3 config

[S3 Config]
1) S3 config must be placed at config/s3_<config_file_name>
2) <config-file-name> is typically <feed-name>_config.json
3) Config must be json with the root object being an associative array
4) Config must include the following key/value pairs:
 - aws_access_key_id: str -> AWS secret key ID generated for AWS IAM user
 - aws_secret_access_key: str -> AWS secret access key generated for AWS IAM user
 - s3_bucket: str -> name of S3 bucket
 - s3_filename: str -> config file name in S3 bucket root

See config/s3_<feed-name>_config.json.template for a more visual example.
