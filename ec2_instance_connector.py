import paramiko
import time
import os
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())


def ssh_connect_with_retry(ssh, ip_address, retries):
    if retries > 3:
        return False
    privkey = paramiko.RSAKey.from_private_key_file('configs/proshchy_capstone_ec2.pem')
    interval = 10
    try:
        retries += 1
        print('SSH into the instance: {}'.format(ip_address))
        ssh.connect(hostname=ip_address,
                    username='ec2-user', pkey=privkey)
        return True
    except Exception as e:
        print(e)
        time.sleep(interval)
        print('Retrying SSH connection to {}'.format(ip_address))
        ssh_connect_with_retry(ssh, ip_address, retries)


# print(os.getenv('ec2_instance_id'))
# ssh_connect_with_retry(ssh, 'ec2-18-223-247-115.us-east-2.compute.amazonaws.com', 0)
#
# stdin, stdout, stderr = ssh.exec_command("ls -l")
# print('stdout:', stdout.read())
# print('stderr:', stderr.read())
# ssh.close()