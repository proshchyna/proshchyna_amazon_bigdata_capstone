import psycopg2


def get_postgres_connection():
	conn = psycopg2.connect(host='proshchy-capstone-db.cnz7flo1slhx.us-east-2.rds.amazonaws.com',
							port=5432,
							database='postgres',
							user='proshchyna',
							password='111proshchyna1111')

	cur = conn.cursor()
	# cur.execute("SELECT version()")
	# cur.fetchone()
	# ('PostgreSQL 12.4 on x86_64-pc-linux-gnu, compiled by gcc (GCC) 4.8.3 20140911 (Red Hat 4.8.3-9), 64-bit',)
	# cur.execute("SELECT * from postgres")