import boto3

# s3_client = boto3.client('s3')

# result = s3_client.create_bucket(Bucket='test_delete_me_please')


def create_key_pair(key_pair_name: str) -> None:
	client = boto3.client('ec2')
	response = client.create_key_pair(KeyName=key_pair_name)

	with open(f'{response["KeyName"]}.pem', 'w+') as f:
		f.write(response['KeyMaterial'])


def launch_ec2_instance(meta):
	ec2 = boto3.resource('ec2')

	response = ec2.create_instances(
		ImageId='ami-09558250a3419e7d0',
		MinCount=1,
		MaxCount=1,
		InstanceType='t2.micro',
		KeyName=meta['KeyPairName'],
	)

	instance_id = response[0].id
	response[0].create_tags(Resources=['i-0fe9f1b4f3bfb4d43'],
							Tags=[{'Key': 'Name', 'Value': 'proshchy_capstone_ec2_instance'}])
	return instance_id


def launch_rds(meta):
	client = boto3.client('rds')

	client.create_db_instance(DBInstanceIdentifier=meta['DBInstanceIdentifier'],
							  DBInstanceClass='db.t2.micro',
							  Engine='postgres',
							  MasterUsername=meta['MasterUsername'],
							  MasterUserPassword=meta['MasterUserPassword'],
							  AllocatedStorage=10)
	print("Postgres instance created!")


def clean_infrastructure(meta):
	try:
		resource = boto3.resource('ec2')
		key_pair = resource.KeyPair(meta['KeyPairName'])
		key_pair_id = key_pair.key_pair_id
		key_pair.delete()
	except:
		pass
	finally:
		print(f"Key Pair {meta['KeyPairName']} removed!")

	client = boto3.client('ec2')
	result = client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [meta['ec2_instance_name']]}])

	instances_to_terminate = []
	for group in result['Reservations']:
		for instance in group['Instances']:
			instances_to_terminate.append(instance['InstanceId'])

	client.terminate_instances(InstanceIds=instances_to_terminate)
	print("EC2 instances terminated!")

	client = boto3.client('rds')
	client.delete_db_instance(DBInstanceIdentifier=meta['DBInstanceIdentifier'], SkipFinalSnapshot=True)
	print("Postgres instance deleted!")


def main():
	meta = {'KeyPairName': 'proshchy_capstone_ec2',
			'ec2_instance_name': 'proshchy_capstone_ec2_instance',
			'DBInstanceIdentifier': 'proshchy-capstone-db',
			'MasterUsername': 'proshchyna',
			'MasterUserPassword': '111proshchyna1111'
			}

	clean_infrastructure(meta)

	# create_key_pair(key_pair_name=meta['KeyPairName'])
	#
	# instance_id = launch_ec2_instance(meta)
	# meta['ec2_instance_id'] = instance_id

# {'DBInstances': [{'DBInstanceIdentifier': 'proshchy-capstone-db', 'DBInstanceClass': 'db.t2.micro', 'Engine': 'postgres', 'DBInstanceStatus': 'available', 'MasterUsername': 'proshchyna', 'Endpoint': {'Address': 'proshchy-capstone-db.cnz7flo1slhx.us-east-2.rds.amazonaws.com', 'Port': 5432, 'HostedZoneId': 'Z2XHWR1WZ565X2'}, 'AllocatedStorage': 10, 'InstanceCreateTime': datetime.datetime(2020, 11, 28, 14, 35, 3, 110000, tzinfo=tzutc()), 'PreferredBackupWindow': '10:04-10:34', 'BackupRetentionPeriod': 1, 'DBSecurityGroups': [], 'VpcSecurityGroups': [{'VpcSecurityGroupId': 'sg-29509c4e', 'Status': 'active'}], 'DBParameterGroups': [{'DBParameterGroupName': 'default.postgres12', 'ParameterApplyStatus': 'in-sync'}], 'AvailabilityZone': 'us-east-2c', 'DBSubnetGroup': {'DBSubnetGroupName': 'default', 'DBSubnetGroupDescription': 'default', 'VpcId': 'vpc-6add1d01', 'SubnetGroupStatus': 'Complete', 'Subnets': [{'SubnetIdentifier': 'subnet-5bc54c17', 'SubnetAvailabilityZone': {'Name': 'us-east-2c'}, 'SubnetOutpost': {}, 'SubnetStatus': 'Active'}, {'SubnetIdentifier': 'subnet-c2c4e2b8', 'SubnetAvailabilityZone': {'Name': 'us-east-2b'}, 'SubnetOutpost': {}, 'SubnetStatus': 'Active'}, {'SubnetIdentifier': 'subnet-ea20c881', 'SubnetAvailabilityZone': {'Name': 'us-east-2a'}, 'SubnetOutpost': {}, 'SubnetStatus': 'Active'}]}, 'PreferredMaintenanceWindow': 'fri:03:12-fri:03:42', 'PendingModifiedValues': {}, 'LatestRestorableTime': datetime.datetime(2020, 11, 28, 15, 16, 15, tzinfo=tzutc()), 'MultiAZ': False, 'EngineVersion': '12.4', 'AutoMinorVersionUpgrade': True, 'ReadReplicaDBInstanceIdentifiers': [], 'LicenseModel': 'postgresql-license', 'OptionGroupMemberships': [{'OptionGroupName': 'default:postgres-12', 'Status': 'in-sync'}], 'PubliclyAccessible': True, 'StorageType': 'gp2', 'DbInstancePort': 0, 'StorageEncrypted': False, 'DbiResourceId': 'db-F3DGJ3VTBFZX7JRMCTF4G3XULQ', 'CACertificateIdentifier': 'rds-ca-2019', 'DomainMemberships': [], 'CopyTagsToSnapshot': False, 'MonitoringInterval': 0, 'DBInstanceArn': 'arn:aws:rds:us-east-2:571632058847:db:proshchy-capstone-db', 'IAMDatabaseAuthenticationEnabled': False, 'PerformanceInsightsEnabled': False, 'DeletionProtection': False, 'AssociatedRoles': [], 'TagList': []}, {'DBInstanceIdentifier': 'vkharchenko-db-cluster-instance-1', 'DBInstanceClass': 'db.r5.large', 'Engine': 'aurora-mysql', 'DBInstanceStatus': 'stopped', 'MasterUsername': 'admin', 'DBName': 'vkharchenko_db', 'Endpoint': {'Address': 'vkharchenko-db-cluster-instance-1.cnz7flo1slhx.us-east-2.rds.amazonaws.com', 'Port': 3306, 'HostedZoneId': 'Z2XHWR1WZ565X2'}, 'AllocatedStorage': 1, 'InstanceCreateTime': datetime.datetime(2020, 11, 22, 19, 44, 51, 971000, tzinfo=tzutc()), 'PreferredBackupWindow': '04:02-04:32', 'BackupRetentionPeriod': 1, 'DBSecurityGroups': [], 'VpcSecurityGroups': [{'VpcSecurityGroupId': 'sg-29509c4e', 'Status': 'active'}], 'DBParameterGroups': [{'DBParameterGroupName': 'default.aurora-mysql5.7', 'ParameterApplyStatus': 'in-sync'}], 'AvailabilityZone': 'us-east-2b', 'DBSubnetGroup': {'DBSubnetGroupName': 'default-vpc-6add1d01', 'DBSubnetGroupDescription': 'Created from the RDS Management Console', 'VpcId': 'vpc-6add1d01', 'SubnetGroupStatus': 'Complete', 'Subnets': [{'SubnetIdentifier': 'subnet-5bc54c17', 'SubnetAvailabilityZone': {'Name': 'us-east-2c'}, 'SubnetOutpost': {}, 'SubnetStatus': 'Active'}, {'SubnetIdentifier': 'subnet-c2c4e2b8', 'SubnetAvailabilityZone': {'Name': 'us-east-2b'}, 'SubnetOutpost': {}, 'SubnetStatus': 'Active'}, {'SubnetIdentifier': 'subnet-ea20c881', 'SubnetAvailabilityZone': {'Name': 'us-east-2a'}, 'SubnetOutpost': {}, 'SubnetStatus': 'Active'}]}, 'PreferredMaintenanceWindow': 'sat:04:37-sat:05:07', 'PendingModifiedValues': {}, 'MultiAZ': False, 'EngineVersion': '5.7.mysql_aurora.2.07.2', 'AutoMinorVersionUpgrade': True, 'ReadReplicaDBInstanceIdentifiers': [], 'LicenseModel': 'general-public-license', 'OptionGroupMemberships': [{'OptionGroupName': 'default:aurora-mysql-5-7', 'Status': 'in-sync'}], 'PubliclyAccessible': False, 'StorageType': 'aurora', 'DbInstancePort': 0, 'DBClusterIdentifier': 'vkharchenko-db-cluster', 'StorageEncrypted': True, 'KmsKeyId': 'arn:aws:kms:us-east-2:571632058847:key/b2868566-70e3-4c02-b5ee-9be476768525', 'DbiResourceId': 'db-KOUEGMQYXZ7Q4H6LNHQBANOH4A', 'CACertificateIdentifier': 'rds-ca-2019', 'DomainMemberships': [], 'CopyTagsToSnapshot': False, 'MonitoringInterval': 0, 'MonitoringRoleArn': 'arn:aws:iam::571632058847:role/rds-monitoring-role', 'PromotionTier': 1, 'DBInstanceArn': 'arn:aws:rds:us-east-2:571632058847:db:vkharchenko-db-cluster-instance-1', 'IAMDatabaseAuthenticationEnabled': False, 'PerformanceInsightsEnabled': True, 'PerformanceInsightsKMSKeyId': 'arn:aws:kms:us-east-2:571632058847:key/b2868566-70e3-4c02-b5ee-9be476768525', 'PerformanceInsightsRetentionPeriod': 7, 'DeletionProtection': False, 'AssociatedRoles': [], 'TagList': []}], 'ResponseMetadata': {'RequestId': 'a0c18a3a-0c74-403d-9b58-dfe2720db0ff', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': 'a0c18a3a-0c74-403d-9b58-dfe2720db0ff', 'content-type': 'text/xml', 'content-length': '9414', 'vary': 'accept-encoding', 'date': 'Sat, 28 Nov 2020 15:22:31 GMT'}, 'RetryAttempts': 0}}
if __name__ == '__main__':
	main()
