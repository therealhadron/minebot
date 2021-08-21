import boto3
from botocore.exceptions import ClientError
import json
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "./vendored"))
import requests

region = 'us-east-1'
ec2 = boto3.client('ec2', region_name=region)
ec2_resource = boto3.resource('ec2')

key_Name = 'minebot_server_key'
security_group_name = 'minebot_security'

TOKEN = os.environ['TELEGRAM_TOKEN']
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

def handler(event, context):
    data = json.loads(event["body"])
    message = str(data["message"]["text"])
    chat_id = data["message"]["chat"]["id"]

    if message == "startInstance":
        createSecurityGroup()
        sendMessage("Security group created!", chat_id)
        createKeyPair()
        sendMessage("Key pair created!", chat_id)
        createInstance()
        sendMessage("Successfully started instance!", chat_id)

    sendMessage(message, chat_id)
    return {"statusCode":200}

def sendMessage(message, chat_id):
    url = BASE_URL + "/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message
    }

    res = requests.post(url, data)
    res.raise_for_status()


def get_instance_ids():

    all_instances = ec2.describe_instances()
    
    instance_ids = []
    
    # find instance-id based on instance name
    # many for loops but should work
    for reservation in all_instances['Reservations']:
        for instance in reservation['Instances']:
            if 'Tags' in instance:
                for tag in instance['Tags']:
                    instance_ids.append(instance['InstanceId'])
                        
    return instance_ids

def createKeyPair():
    ec2.create_key_pair(KeyName = key_Name)

# def createKeyPairFile():
#     file = open(f"{key_Name}.pem", 'w')
#     file.write(createKeyPair())
#     file.close
#     return file

def createSecurityGroup():
    security_group = ec2.create_security_group(
        GroupName = security_group_name,
        Description = 'minebot_security_group',
        VpcId = 'vpc-be6212c3'
    )
    ec2.authorize_security_group_ingress(
        GroupId = security_group['GroupId'],
            IpPermissions = [
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }
            ]
    )

def createInstance():
    instance = ec2_resource.create_instances(
        ImageId = 'ami-0c2b8ca1dad447f8a',
        MinCount = 1,
        MaxCount = 1,
        InstanceType = 't2.micro',
        KeyName = key_Name,
        BlockDeviceMappings = [
            {
                'DeviceName': "/dev/xvda",
                'Ebs':{
                    'DeleteOnTermination': True,
                    'VolumeSize': 8
                }
            }
        ],
        SecurityGroups = [security_group_name]
    )