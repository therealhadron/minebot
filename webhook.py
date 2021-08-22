import boto3
from botocore.exceptions import ClientError
import logging
logger = logging.getLogger("webhook")
logging.basicConfig(level=logging.DEBUG)
import os, sys
import json
import requests
import traceback

from core.rcon import send_command

try:
    TOKEN = os.environ['TELEGRAM_TOKEN']
except:
    logger.error(f"Failed to get telegram token from env, is it set? Error: {traceback.format_exc()}")
    TOKEN = ""

REGION = 'us-east-1'
EC2 = boto3.client('ec2', region_name=REGION)
EC2_RESOURCE = boto3.resource('ec2')

KEY_NAME = 'minebot_server_key'
SECURITY_GROUP_NAME = 'minebot_security'

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

    all_instances = EC2.describe_instances()
    
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
    # check to see if key pair already exists
    EC2.create_key_pair(KeyName = KEY_NAME)

def createSecurityGroup():

    # check to see if security group already exists

    security_group = EC2.create_security_group(
        GroupName = SECURITY_GROUP_NAME,
        Description = 'minebot_security_group',
        VpcId = 'vpc-be6212c3'
    )
    EC2.authorize_security_group_ingress(
        GroupId = security_group['GroupId'],
            IpPermissions = [
                {
                    # for ssh
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                },
                {
                    # for minecraft server
                    'IpProtocol': 'tcp',
                    'FromPort': 25565,
                    'ToPort': 25565,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                },
                {
                    # for google drive http requests
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                }
            ]
    )

def createInstance():
    instance = EC2_RESOURCE.create_instances(
        ImageId = 'ami-0c2b8ca1dad447f8a',
        MinCount = 1,
        MaxCount = 1,
        InstanceType = 't2.micro',
        KeyName = KEY_NAME,
        BlockDeviceMappings = [
            {
                'DeviceName': "/dev/xvda",
                'Ebs':{
                    'DeleteOnTermination': True,
                    'VolumeSize': 8
                }
            }
        ],
        SecurityGroups = [SECURITY_GROUP_NAME]
    )