from dotenv import load_dotenv
import os

dotenv_path = 'configs/.env'
load_dotenv(dotenv_path)

if not os.path.exists('data/reviews') or not os.path.exists('data/views'):
	os.makedirs('data/reviews')
	os.makedirs('data/views')
