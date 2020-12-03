from dotenv import load_dotenv
import os

dotenv_path = 'configs/.env'
load_dotenv(dotenv_path)

try:
	if not os.path.exists('/opt/capstone/views') or not os.path.exists('/opt/capstone/reviews'):
		os.makedirs('/opt/capstone/reviews')
		os.makedirs('/opt/capstone/views')
except:
	pass
