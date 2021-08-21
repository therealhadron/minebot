import boto3
from botocore.exceptions import ClientError
import logging
logger = logging.getLogger("webhook")
logging.basicConfig(level=logging.DEBUG)
import os, sys
import json
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "./vendored"))
import requests
import traceback

from core.rcon import send_command

try:
    TOKEN = os.environ['TELEGRAM_TOKEN']
except:
    logger.error(f"Failed to get telegram token from env, is it set? Error: {traceback.format_exc()}")
    TOKEN = ""

region = 'us-east-1'
ec2 = boto3.client('ec2', region_name=region)
ec2_resource = boto3.resource('ec2')

key_Name = 'minebot_server_key'
security_group_name = 'minebot_security'

TOKEN = os.environ['TELEGRAM_TOKEN']
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

def handler(event, context):
    try:
        data = json.loads(event["body"])
        message = str(data["message"]["text"])
        chat_id = data["message"]["chat"]["id"]

        logger.info(f"Received message: {message}")
        command_prefix = "/cmd"
        if message.startswith(command_prefix):
            _send_minecraft_command(chat_id, message[len(command_prefix):])
        elif message.startswith("/start_server"):
            _start_minecraft_server(chat_id)
        elif message.startswith("/stop_server"):
            _send_minecraft_command(chat_id, "stop")
        elif message == "startInstance":
            createSecurityGroup()
            send_telegram_message(chat_id, "Security group created!")
            createKeyPair()
            send_telegram_message(chat_id, "Key pair created!")
            createInstance()
            send_telegram_message(chat_id, "Successfully started instance!")
        else:
            send_telegram_message(chat_id, f"Command not recognized: '{message}'")
    except Exception as e:
        logger.error(f"Request failed with error: {traceback.format_exc()}")
    finally:
        return {"statusCode":200}

def _start_minecraft_server(chat_id: str):
    send_telegram_message(chat_id, "This is where lambda starts up the EC2 instance")

def _send_minecraft_command(chat_id: str, cmd: str):
    if not cmd:
        send_telegram_message(chat_id, "Cannot send empty command")
        return
    try:
        cmd = cmd.strip()
        response = send_command(cmd) or "<No Response>"
        send_telegram_message(chat_id, f"Server response: '{response}'")
    except Exception as e:
        logger.error(f"Failed to send command to Minecraft. Got error: {traceback.format_exc()}")
        send_telegram_message(chat_id, "Failed to send command, is the server on?")
    return {"statusCode":200}

def send_telegram_message(chat_id: str, message: str):
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
