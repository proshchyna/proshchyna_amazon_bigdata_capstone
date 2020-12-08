sudo yum -y install python3
sudo yum -y install git

# fix weird bug with yum
cd /var/run && rm -f yum.pid
cd /home/ec2-user && git clone https://github.com/proshchyna/proshchyna_amazon_bigdata_capstone.git
python3 -m venv proshchyna_amazon_bigdata_capstone/venv
source proshchyna_amazon_bigdata_capstone/venv/bin/activate && pip install -r proshchyna_amazon_bigdata_capstone/requirements.txt
#set -a; source .env; set +a

sudo mkdir /tmp/capstone/ && sudo mkdir /tmp/capstone/views && sudo mkdir /tmp/capstone/reviews
sudo chmod -R 777 /tmp/capstone
source proshchyna_amazon_bigdata_capstone/venv/bin/activate && cd proshchyna_amazon_bigdata_capstone/ && python data_generator.py

# install and set up kinesis agent
sudo yum -y install aws-kinesis-agent
sudo mv /home/ec2-user/agent.json /etc/aws-kinesis/agent.json
sudo service aws-kinesis-agent restart

echo "* * * * * source proshchyna_amazon_bigdata_capstone/venv/bin/activate && cd proshchyna_amazon_bigdata_capstone/ && python data_generator.py" >> jobs.txt
crontab jobs.txt
