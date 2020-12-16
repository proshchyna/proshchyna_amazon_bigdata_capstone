import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from awsglue.job import Job

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

views_df = glueContext.create_dynamic_frame.from_catalog(database="proshchy-capstone", table_name="views_2020").toDF()
print(views_df.count())
ips_df = glueContext.create_dynamic_frame.from_catalog(database="proshchy-capstone", table_name="proshchy_capstone_fraudulent_ip").toDF()
print(ips_df.count())

views_df.createOrReplaceTempView('views')
ips_df.createOrReplaceTempView('bad_ips')

filtered_df = spark.sql("SELECT * FROM views WHERE ip NOT IN (SELECT ip FROM bad_ips)")

print(filtered_df.count())
filtered_dynf = DynamicFrame.fromDF(filtered_df, glueContext, "filtered_views")

glueContext.write_dynamic_frame.from_options(
    frame=filtered_dynf,
    connection_type="s3",
    connection_options={"path": "s3://proshchy-capstone/filtered_views/"},
    format="json")

# job.commit()