sudo yum -y update
sudo yum -y install python3
sudo yum -y install git

git clone https://github.com/proshchyna/proshchyna_amazon_bigdata_capstone.git
python3 -m venv proshchyna_amazon_bigdata_capstone/venv
source proshchyna_amazon_bigdata_capstone/venv/bin/activate
pip install -r proshchyna_amazon_bigdata_capstone/requirements.txt
#set -a; source .env; set +a
python proshchyna_amazon_bigdata_capstone/data_generator.py