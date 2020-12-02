import boto3
from data_generator import get_postgres_connection
from time import sleep
import settings
import os
import psycopg2
# s3_client = boto3.client('s3')

# result = s3_client.create_bucket(Bucket='test_delete_me_please')


def create_key_pair(key_pair_name: str) -> None:
	client = boto3.client('ec2')
	response = client.create_key_pair(KeyName=key_pair_name)

	with open(f'{response["KeyName"]}.pem', 'w+') as f:
		f.write(response['KeyMaterial'])


def launch_ec2_instance():
	ec2 = boto3.resource('ec2')

	response = ec2.create_instances(
		ImageId='ami-09558250a3419e7d0',
		MinCount=1,
		MaxCount=1,
		InstanceType='t2.micro',
		KeyName=os.environ.get('KeyPairName'),
	)

	instance_id = response[0].id
	response[0].create_tags(Resources=[instance_id],
							Tags=[{'Key': 'Name', 'Value': 'proshchy_capstone_ec2_instance'}])
	print(f"EC2 instance: {instance_id} launched!")
	return instance_id


def launch_rds():
	from random import choices
	import string
	import json

	client = boto3.client('rds')
	dynamodb = boto3.client('dynamodb')
	secretsmanager = boto3.client('secretsmanager')

	db_password = ''.join(choices(string.ascii_uppercase + string.digits, k=14))
	client.create_db_instance(DBInstanceIdentifier=os.environ.get('DBInstanceIdentifier'),
							  DBInstanceClass='db.t2.micro',
							  Engine='postgres',
							  MasterUsername=os.environ.get('MasterUsername'),
							  MasterUserPassword=db_password,
							  AllocatedStorage=10)

	try:
		secretsmanager.create_secret(SecretId=os.environ.get('SecretId'),
							 SecretString=json.dumps({"name": os.environ.get('MasterUsername'), "password": db_password}))
	except:
		secretsmanager.update_secret(SecretId=os.environ.get('SecretId'),
							 SecretString=json.dumps({"name": os.environ.get('MasterUsername'), "password": db_password}))

	while True:
		db_info = client.describe_db_instances(DBInstanceIdentifier=os.environ.get('DBInstanceIdentifier'))
		status = db_info['DBInstances'][0]['DBInstanceStatus']
		if status == 'available':
			break
		sleep(5)

	db_info = client.describe_db_instances(DBInstanceIdentifier=os.environ.get('DBInstanceIdentifier'))
	host = db_info['DBInstances'][0]['Endpoint']['Address']
	dynamodb.put_item(TableName=os.environ.get('DynamoDb_table_name'), Item={'PostgresHost': {'S': host}, 'id': {'N': '1'}})

	print("Postgres instance created!")


def create_table_in_rds():
	create_table_statement = """CREATE TABLE IF NOT EXISTS ITEM(
	ITEM_ID 		SERIAL 		PRIMARY KEY,
	TITLE           CHAR(50)    NOT NULL,
	DESCRIPTION		TEXT,
	CATEGORY        CHAR(50)	NOT NULL);
	"""
	try:
		connection = get_postgres_connection()
		cursor = connection.cursor()
		cursor.execute(create_table_statement)
	except(Exception, psycopg2.DatabaseError) as error:
		print("Error while creating PostgreSQL table", error)
	finally:
		cursor.close()
		connection.commit()


def create_metadata_table_in_dynamodb(table_name='proshchy_capstone_metadata'):
	client = boto3.client('dynamodb')
	client.create_table(AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'N'}],
						TableName=table_name,
						KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
						BillingMode='PAY_PER_REQUEST')

	print("Meta data table was created in DynamoDB!")


def clean_ec2():
	try:
		resource = boto3.resource('ec2')
		key_pair = resource.KeyPair(os.environ.get('KeyPairName'))
		key_pair_id = key_pair.key_pair_id
		key_pair.delete()
	except:
		pass
	finally:
		print(f"Key Pair {os.environ.get('KeyPairName')} removed!")

	client = boto3.client('ec2')
	result = client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [os.environ.get('ec2_instance_name')]}])

	instances_to_terminate = []
	for group in result['Reservations']:
		for instance in group['Instances']:
			instances_to_terminate.append(instance['InstanceId'])
	if instances_to_terminate:
		client.terminate_instances(InstanceIds=instances_to_terminate)
		print("EC2 instances terminated!")
	else:
		print("Have no running EC2 instances!")


def clean_rds():
	try:
		client = boto3.client('rds')
		client.delete_db_instance(DBInstanceIdentifier=os.environ.get('DBInstanceIdentifier'), SkipFinalSnapshot=True)

		while True:
			try:
				client.describe_db_instances(DBInstanceIdentifier=os.environ.get('DBInstanceIdentifier'))
			except:
				break
			sleep(10)
			print("DB is not deleted yet")
		print("Postgres instance deleted!")
	except:
		print("Have no RDS to delete!")


def clean_dynamodb():
	try:
		client = boto3.client('dynamodb')
		client.delete_table(TableName=os.environ.get('DynamoDb_table_name'))
		print('proshchy_capstone_metadata table deleted from DynamoDB')
		sleep(10)
	except:
		print("Nothing to clean in DynamoDB!")


def clean_infrastructure():
	clean_ec2()
	# clean_rds()
	# clean_dynamodb()


def main():
	print(os.environ.get("KeyPairName"))
	clean_infrastructure()
	# create_metadata_table_in_dynamodb()

	create_key_pair(key_pair_name=os.environ.get('KeyPairName'))

	instance_id = launch_ec2_instance()
	os.environ['ec2_instance_id'] = instance_id
	print(os.environ.get('ec2_instance_id'))
	# launch_rds(meta)
	# create_table_in_rds()


if __name__ == '__main__':
	main()
