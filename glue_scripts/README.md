These scripts uses for creating pipeline in GLue.

- `filter_views.py` - Filter out views that contains fraudulent ips and store them to S3 bucket `filtered_views/`
- `write_fraudulent_ips_to_db` - Selects fraudulent ips from views and store them to DynamoDb.
