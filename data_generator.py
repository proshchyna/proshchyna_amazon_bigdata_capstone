import psycopg2
import boto3
import json
import settings
import os


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
				print(data[0], data[1], data[2], data[3].replace('\n', ''))
			line_counter += 1
		cursor.close()
		connection.commit()


if __name__ == "__main__":
	upload_items_to_postgres()