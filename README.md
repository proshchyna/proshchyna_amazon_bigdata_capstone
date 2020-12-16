# proshchyna_amazon_bigdata_capstone
### How to check?

1. Set up configs/.aws/config and configs/.aws/credentials
2. Run aws_infrastructure.py

EMR + Spark + Glue task done using AWS UI 

Tasks
### You should calculate the following statistics:
- Generate source data(EC2, Python, Kinesis Firehose)
- Identify suspicious IPs, based on item’s views (criteria is pretty simple: more than 5 view events per second on average from particular IP)
(EMR PySpark notebook, S3)
- Filter out suspicious IPs from views and reviews data(GLue Job + S3)
- Identify the most popular items by views(Redshift)
- Identify the most popular categories by views(Redshift)
- Collect distribution of views by device types(EMR PySpark Notebook)
- Identify reviews, which contains spam content. Mark them with the corresponding label
- Collect average ratings for items, based on non-spam reviews, which contains not empty title and text
