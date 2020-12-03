"""
This script generates data for a capstone project.

There are three modes of operation:

`batch` - generates a batch of logs with timestamps from the previous hour in CSV format and uploads it to S3
`stream items` - streams item view logs continuously into Kinesis
`stream reviews` - streams review logs continuously into Kinesis

Note, that this script stores generated users and items in CSV files in its working directory and automatically picks
it up from there, so items/users persist across multiple runs. To re-generate them, remove/rename these CSV files.

Most of the behaviour can be controlled by tweaking global variables below. You'll need to update some of them
(Kinesis stream/S3 bucket) to your own.
"""

import io
import json
import os
import random
import time
import shutil
import subprocess
import sys

from datetime import datetime, timedelta

# S3_BUCKET = "<your S3 bucket>"
# S3_PREFIX = "<your prefix>"
#
# KINESIS_ITEM_STREAM = "<your kinesis stream for item purchase events>"
# KINESIS_REVIEW_STREAM = "<your kinesis stream for review events>"
#
# N_USERS = 50
N_ITEMS = 100
# BOT_PROBABILITY = 0.1
#
ITEMS_FILE = "items.csv"
# USERS_FILE = "users.csv"
#
# TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def generate_item(item_id):
    title = "item #{}".format(item_id)
    description = "description of item {}".format(item_id)
    category = random.randint(1, 13)
    return str(item_id), title, description, str(category)


def generate_or_load(filename, generator, header=None, force=False):
    if os.path.exists(filename) and not force:
        with open(filename) as f:
            items = [line.split(",") for line in f.read().splitlines()][1 if header else 0:]
    else:
        items = generator()
        with open(filename, "w") as f:
            if header is not None:
                f.write(header + '\n')
            f.write("\n".join((",".join(i) for i in items)))
    return items


def generate_or_load_items(n):
    return generate_or_load(ITEMS_FILE, lambda: [
        generate_item(i)
        for i in range(1000, 1000 + n)
    ], header="item_id,title,description,category", force=False)


def sleep_until(t):
    now = datetime.now()
    if t > now:
        time.sleep((t - now).total_seconds())


# def stream_to_kinesis(stream, log_generator):
#     import boto3
#     from kiner.producer import KinesisProducer
#
#     producer = KinesisProducer(
#         stream_name=stream,
#         batch_size=100,
#         batch_time=1,
#         max_retries=10,
#         kinesis_client=boto3.client("kinesis", region_name="us-east-1")
#     )
#
#     try:
#         while True:
#             logs = log_generator()
#
#             for record in logs:
#                 next_record_ts = datetime.strptime(json.loads(record)["ts"], TS_FORMAT)
#                 sleep_until(next_record_ts)
#                 print(record)
#                 producer.put_record(record + "\n")
#     finally:
#         producer.close()


# def generate_batch(users, items):
#     import boto3
#
#     prev_hour = datetime.now().replace(microsecond=0, second=0, minute=0) - timedelta(hours=1)
#     logs = generate_logs(users, prev_hour, lambda *a: line_generator_item_access(*a, items=items))
#     logs_as_csv_string = "\n".join((",".join(line) for line in logs))
#
#     s3 = boto3.client("s3")
#
#     with io.BytesIO(logs_as_csv_string.encode('utf-8')) as f:
#         s3.upload_fileobj(f, S3_BUCKET, S3_PREFIX + prev_hour.strftime("/%Y/%m/%d/%H.csv"))
