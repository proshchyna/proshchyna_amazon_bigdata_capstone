# proshchyna_amazon_bigdata_capstone
### How to set up?

1. Create AWS credentials under configs/.aws/config and configs/.aws/credentials
2. Change .env file if needed.(Use for storing service names and other not secret info)
2. Run aws_infrastructure.py

### Project description
#### You should calculate the following statistics:
- Generate source data(EC2, Python, Kinesis Firehose)
- Identify suspicious IPs, based on item’s views (criteria is pretty simple: more than 5 view events per second on average from particular IP)
- Filter out suspicious IPs from views and reviews data.
- Identify the most popular items by views(Redshift)
- Identify the most popular categories by views(Redshift)
- Collect distribution of views by device types(Redshift)
- Identify reviews, which contains spam content. Mark them with the corresponding label
- Collect average ratings for items, based on non-spam reviews, which contains not empty title and text

### Solution:
1. Running aws_infrastructure.py you will set up EC2 instance, IAM role, Kinesis Stream, S3 buckets, DynamoDB, RDS(Postgres) and SecretManagers.
Once these stuff ready, script will install and deploy data generator with needed dependencies and start aws-kinesis-agent.
Kinesis streams data directly to S3 Buckets 'views' and 'reviews'.
2. Identify suspicious IPs, based on item’s views: done using Glue(jobs, triggers), EMR, PySpark and S3.
3. Filter out suspicious IPs from views and reviews data: GLue Job + S3.
4. Identify the most popular items by views: Created external table in Redshift and prepared query.
5. Identify the most popular categories by views: Created external table in Redshift and prepared query.
6. Collect distribution of views by device types: Query in Redshift.