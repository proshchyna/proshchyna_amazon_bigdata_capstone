from pyspark.sql.functions import from_unixtime, col
from datetime import datetime

import sys
# from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from awsglue.job import Job

# sc.install_pypi_package('boto3')
import boto3

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)


def get_suspicious_ips(df):
    df.createOrReplaceTempView('VIEW')
    counted_ips_df = spark.sql("select ip, count(*) as amount from view group by timestamp, ip having amount > 5 order by amount DESC")
    ips = counted_ips_df.select('ip')
    ips = ips.collect()
    return [row.ip for row in ips]


def put_item_into_dynamodb(item, table_name):
    client = boto3.client('dynamodb',  region_name='us-east-2')
    client.put_item(TableName='proshchy_capstone_fraudulent_ip',
                Item=item)
    # print(f"{item} in db!")


if __name__ == '__main__':
    df = spark.read.json('s3://proshchy-capstone/views_2020/12/*/*/*')
    df = df.withColumn('timestamp', from_unixtime('date_timestamp', "dd/MM/yyyy HH:MM:SS"))

    ips = get_suspicious_ips(df)

    for ip in ips:
        put_item_into_dynamodb(item={'ip': {'S': ip}}, table_name='proshchy_capstone_fraudulent_ip')