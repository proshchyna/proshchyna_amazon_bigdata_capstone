import psycopg2
import boto3
import json
import os
from faker import Faker
from datetime import datetime, timedelta
import random
import configs.settings
from generate_items import generate_or_load_items


def generate_items_if_needed(size):
	if not os.path.exists('items.csv'):
		generate_or_load_items(size)


def get_postgres_connection():
	secretsmanager = boto3.client('secretsmanager')
	dynamodb = boto3.client('dynamodb')

	creds = secretsmanager.get_secret_value(SecretId=os.environ.get('SecretId'))
	creds = json.loads(creds['SecretString'])
	host = dynamodb.get_item(TableName=os.environ.get('DynamoDb_table_name'), Key={'id': {'N': '1'}})
	host = host['Item']['PostgresHost']['S']

	conn = psycopg2.connect(host=host,
							port=5432,
							database='postgres',
							user=creds['name'],
							password=creds['password'])
	return conn


def upload_items_to_postgres():
	insert_statement = "INSERT INTO item (title, description, category) values ('{}', '{}', '{}')"
	with open('items.csv') as items:
		connection = get_postgres_connection()
		cursor = connection.cursor()
		line_counter = 0

		for line in items.readlines():
			if line_counter > 0:
				data = line.split(',')
				cursor.execute(insert_statement.format(data[1], data[2], data[3].replace('\n', '')))
			line_counter += 1
		cursor.close()
		connection.commit()


def get_item_ids_from_postgres() -> list:
	connection = get_postgres_connection()
	cursor = connection.cursor()

	cursor.execute("SELECT item_id from item;")
	item_ids = [str(item[0]) for item in cursor]
	cursor.close()
	random.shuffle(item_ids)

	return item_ids


def generate_views(size=100, datetime_interval=1):
	faker = Faker()
	item_ids = get_item_ids_from_postgres()
	datetime_start = datetime.now() - timedelta(datetime_interval)
	timestamps = [str(faker.date_time_between_dates(datetime_start=datetime_start).timestamp()) for _ in range(size)]
	user_agents = [faker.user_agent() for _ in range(size)]
	ips = [faker.ipv4() for _ in range(size)]

	views = list(zip(item_ids, timestamps, user_agents, ips))
	header = 'item_id,timestamp,user_agent,ip\n'
	file_prefix = str(datetime.now().timestamp())
	with open(f'/tmp/capstone/views/{file_prefix}_view.csv', 'w+') as views_file:
		views_file.write(header)
		for view in views:
			views_file.write(','.join(view) + '\n')


def generate_reviews(size=100, datetime_interval=1):
	faker = Faker()
	item_ids = get_item_ids_from_postgres()
	datetime_start = datetime.now() - timedelta(datetime_interval)
	timestamps = [str(faker.date_time_between_dates(datetime_start=datetime_start).timestamp()) for _ in range(size)]
	user_agents = [faker.user_agent() for _ in range(size)]
	ips = [faker.ipv4() for _ in range(size)]
	review_titles = [faker.word() for _ in range(size)]
	review_texts = [faker.text(max_nb_chars=200).replace('\n', '') for _ in range(size)]
	stars = [str(faker.random_number(digits=1)) for _ in range(size)]

	reviews = list(zip(item_ids, timestamps, user_agents, ips, review_titles, review_texts, stars))
	header = 'item_id\ttimestamp\tuser_agent\tip\treview_title\treview_text\tstars\n'
	file_prefix = str(datetime.now().timestamp())
	with open(f'/tmp/capstone/reviews/{file_prefix}_reviews.tsv', 'w+') as reviews_file:
		reviews_file.write(header)
		for review in reviews:
			reviews_file.write('\t'.join(review) + '\n')


if __name__ == "__main__":
	generate_items_if_needed(100)
	upload_items_to_postgres()
	# get_item_ids_from_postgres()
	generate_views(size=10)
	generate_reviews(size=10)
