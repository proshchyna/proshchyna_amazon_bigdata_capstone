sudo yum -y install python3
sudo yum -y install git

cd /var/run && rm -f yum.pid
cd /home/ec2-user && git clone https://github.com/proshchyna/proshchyna_amazon_bigdata_capstone.git
python3 -m venv proshchyna_amazon_bigdata_capstone/venv
source proshchyna_amazon_bigdata_capstone/venv/bin/activate && pip install -r proshchyna_amazon_bigdata_capstone/requirements.txt
#set -a; source .env; set +a
source proshchyna_amazon_bigdata_capstone/venv/bin/activate && cd proshchyna_amazon_bigdata_capstone/ && python data_generator.py
