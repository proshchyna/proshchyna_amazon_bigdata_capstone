import boto3
from data_generator import get_postgres_connection
from time import sleep
import os
import psycopg2
import configs.settings
from ec2_instance_connector import ssh_connect_with_retry, ssh
import json


def create_key_pair(key_pair_name: str) -> None:
	client = boto3.client('ec2')
	response = client.create_key_pair(KeyName=key_pair_name)

	key_path = f'configs/{response["KeyName"]}.pem'
	try:
		os.chmod(key_path, 0o777)
	except:
		pass

	with open(key_path, 'w+') as f:
		f.write(response['KeyMaterial'])

	os.chmod(key_path, 0o400)
	print("Key Pair for EC2 instance ready!")


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
							Tags=[{'Key': 'Name', 'Value': os.environ.get('ec2_instance_name')}])

	instance = ec2.Instance(instance_id)
	instance.wait_until_running()
	ip = instance.public_ip_address

	# Associating IAM Role with needed policies to EC2 instance.
	client = boto3.client('ec2')
	client.associate_iam_instance_profile(
		IamInstanceProfile={
			'Name': os.environ.get('ec2_iam_role_profile_name')
		},
		InstanceId=instance_id
	)
	print(f"EC2 instance: {instance_id} launched!")
	return instance_id, ip


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
		sleep(10)
		print("Postgres is not ready yet!")

	db_info = client.describe_db_instances(DBInstanceIdentifier=os.environ.get('DBInstanceIdentifier'))
	host = db_info['DBInstances'][0]['Endpoint']['Address']
	dynamodb.put_item(TableName=os.environ.get('DynamoDb_table_name'), Item={'PostgresHost': {'S': host}, 'id': {'N': '1'}})

	print("Postgres instance ready!")


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
		print("Table in Postgres instance created!")
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
			sleep(20)
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


def clean_kinesis_streams():
	try:
		client = boto3.client('firehose')
		client.delete_delivery_stream(DeliveryStreamName=os.environ.get('kinesis_view_stream_name'))
		print("Kinesis view Stream removed!")
	except:
		print("Has no Kinesis view Stream to delete!")

	try:
		client = boto3.client('firehose')
		client.delete_delivery_stream(DeliveryStreamName=os.environ.get('kinesis_review_stream_name'))
		print("Kinesis review Stream removed!")
	except:
		print("Has no Kinesis review Stream to delete!")


def delete_s3_bucket():
	try:
		s3 = boto3.resource('s3')
		bucket = s3.Bucket(os.environ.get('s3_bucket_name'))
		bucket.objects.all()

		for key in bucket.objects.all():
			key.delete()

		client = boto3.client('s3')
		client.delete_bucket(Bucket=os.environ.get('s3_bucket_name'))
		print("Bucket deleted!")
	except:
		print("Have no S3 Bucket to delete!")


def clean_infrastructure():
	clean_ec2()
	clean_kinesis_streams()
	clean_rds()
	clean_dynamodb()
	delete_s3_bucket()


def configure_ec2_instance():
	ssh_connect_with_retry(ssh, os.environ.get('ec2_ip_address'), 0)
	sftp = ssh.open_sftp()

	ssh.exec_command("mkdir .aws")
	sftp.put(localpath='configs/.aws/config', remotepath='/home/ec2-user/.aws/config')
	sftp.put(localpath='configs/.aws/credentials', remotepath='/home/ec2-user/.aws/credentials')
	sftp.put(localpath='configs/configure_ec2_environment.sh', remotepath='/home/ec2-user/configure_ec2_environment.sh')
	sftp.put(localpath='configs/aws-kinesis-agent.json', remotepath='/home/ec2-user/agent.json')
	stdin, stdout, stderr = ssh.exec_command('sh /home/ec2-user/configure_ec2_environment.sh')
	print('stdout:', stdout.read())
	print('stderr:', stderr.read())
	print("EC2 instance configured successfully!")
	sftp.close()
	ssh.close()


def launch_kinesis_data_stream():
	import boto3
	client_firehose = boto3.client('firehose')
	client_firehose.create_delivery_stream(DeliveryStreamName=os.environ.get('kinesis_view_stream_name'),
										   DeliveryStreamType='DirectPut',
										   S3DestinationConfiguration={
											   'RoleARN': "arn:aws:iam::{}:role/{}"
										   .format(boto3.client('sts').get_caller_identity().get('Account'),
												   os.environ.get('firehose_to_s3_iam_role_name')),
											   'BucketARN': f"arn:aws:s3:::{os.environ.get('s3_bucket_name')}",
											   'Prefix': 'views_'})

	client_firehose.create_delivery_stream(DeliveryStreamName=os.environ.get('kinesis_review_stream_name'),
										   DeliveryStreamType='DirectPut',
										   S3DestinationConfiguration={
											   'RoleARN': "arn:aws:iam::{}:role/{}"
										   .format(boto3.client('sts').get_caller_identity().get('Account'),
												   os.environ.get('firehose_to_s3_iam_role_name')),
											   'BucketARN': f"arn:aws:s3:::{os.environ.get('s3_bucket_name')}",
											   'Prefix': 'reviews_'})
	print(f"Kinesis Delivery Streams launched!")


def creating_iam_roles_with_policies():
	client = boto3.client('iam')
	# Creating IAM Role and Profile for EC2 instance.
	ec2_policies = ['arn:aws:iam::aws:policy/AmazonEC2FullAccess',
					'arn:aws:iam::aws:policy/AmazonS3FullAccess',
					'arn:aws:iam::aws:policy/AmazonKinesisFullAccess',
					'arn:aws:iam::aws:policy/AmazonKinesisFirehoseFullAccess',
					'arn:aws:iam::aws:policy/CloudWatchFullAccess']
	try:
		role_name = os.environ.get('ec2_iam_role_profile_name')
		client.create_instance_profile(InstanceProfileName=role_name)
		client.create_role(RoleName=role_name, AssumeRolePolicyDocument=json.dumps(
			{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "ec2.amazonaws.com"},
													 "Action": "sts:AssumeRole"}]}))

		for police in ec2_policies:
			client.attach_role_policy(RoleName=role_name,
									  PolicyArn=police)

		client.add_role_to_instance_profile(InstanceProfileName=role_name,
											RoleName=role_name)
	except:
		pass

	# Creating IAM role for Firehose to S3 delivery.
	try:
		role_name = os.environ.get('firehose_to_s3_iam_role_name')
		client.create_instance_profile(InstanceProfileName=role_name)
		client.create_role(RoleName=role_name,
						   AssumeRolePolicyDocument=json.dumps(
							   {"Version": "2012-10-17", "Statement": [{"Effect": "Allow",
																		"Principal": {"Service": "firehose.amazonaws.com"},
									 "Action": "sts:AssumeRole"}]}))

		client.attach_role_policy(RoleName=role_name, PolicyArn='arn:aws:iam::aws:policy/AmazonS3FullAccess')
		client.add_role_to_instance_profile(InstanceProfileName=role_name,
											RoleName=role_name)
	except:
		pass


def create_s3_bucket():
	try:
		client = boto3.client('s3')
		client.create_bucket(
			Bucket=os.environ.get('s3_bucket_name'),
			CreateBucketConfiguration={'LocationConstraint': 'us-east-2'}
		)
		print("S3 bucket has been created!")
	except:
		print("S3 bucket already created!")


def main():
	print(os.environ.get("KeyPairName"))
	clean_infrastructure()
	# create_metadata_table_in_dynamodb()

	create_key_pair(key_pair_name=os.environ.get('KeyPairName'))
	creating_iam_roles_with_policies()
	create_s3_bucket()

	instance_id, ip = launch_ec2_instance()
	os.environ['ec2_instance_id'] = instance_id
	os.environ['ec2_ip_address'] = ip

	print(os.environ.get('ec2_instance_id'), os.environ.get('ec2_ip_address'))
	# launch_rds()
	# create_table_in_rds()
	launch_kinesis_data_stream()
	configure_ec2_instance()


if __name__ == '__main__':
	main()
