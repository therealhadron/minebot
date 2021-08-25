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
            if instanceExists():
                if getInstanceInfo("statusCode") == 16:
                    send_telegram_message(chat_id, "Instance already running!")
                elif getInstanceInfo("statusCode") == 80:
                    startInstance()
                    send_telegram_message(chat_id, "Starting instance")
                else:
                    send_telegram_message(chat_id, f"Instance already exists is it is currently: {getInstanceInfo('status')}")
            else:
                if keyPairExists() and securityGroupExists():
                    createInstance()
                    send_telegram_message(chat_id, "Successfully created and started instance!")
                else:
                    send_telegram_message(chat_id, "key pair or security group does not exist creating them now...")
                    if not keyPairExists():
                        createKeyPair()
                        send_telegram_message(chat_id, "Successfully created new key pair")
                    if not securityGroupExists():
                        createSecurityGroup()
                        send_telegram_message(chat_id, "Successfully created new security group")
                    send_telegram_message(chat_id, "Please run 'startInstance' again")
        elif message == "createKeyPair":
            createKeyPair()
            send_telegram_message(chat_id, "Successfully created new key pair")
        elif message == "createSecurityGroup":
            if securityGroupExists():
                send_telegram_message(chat_id, "Security group")
            else:
                createSecurityGroup()
                send_telegram_message(chat_id, "Successfully created new security group")
        elif message == "getInstanceStatus":
            if instanceExists():
                send_telegram_message(chat_id, f"The instance is currently: {getInstanceInfo('status')}")
            else:
                send_telegram_message(chat_id, "No instance exist. Start a new one first")
        elif message == "getInstanceIpAddress":
            if instanceExists() and getInstanceInfo('statusCode') == 16:
                send_telegram_message(chat_id, f"Instance Ip Address is: {getInstanceInfo('ipAddress')}")
            else:
                send_telegram_message(chat_id, "No instance exist or instance is not running. Start a new/start instance first")
        elif message == "stopInstance":
            if stopInstance():
                send_telegram_message(chat_id, "Instance stopping")
            else:
                send_telegram_message(chat_id, "Error stopping instance")
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
    if not keyPairExists():
        EC2.create_key_pair(KeyName = KEY_NAME)

def keyPairExists():
    key_pairs = EC2.describe_key_pairs()['KeyPairs']
    for key in key_pairs:
        if key['KeyName'] == KEY_NAME:
            return True
    return False

def createSecurityGroup():
    security_group = EC2.create_security_group(
        GroupName = SECURITY_GROUP_NAME,
        Description = f"{SECURITY_GROUP_NAME}_group",
        VpcId = str(getVpc())
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

def securityGroupExists():
    security_groups = EC2.describe_security_groups()['SecurityGroups']
    for group in security_groups:
        if str(group['GroupName']) == SECURITY_GROUP_NAME:
            return True
    return False

def getVpc():
    security_groups = EC2.describe_security_groups()['SecurityGroups']
    for group in security_groups:
        if group['GroupName'] == 'default':
            return group['VpcId']

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

def startInstance():
    if instanceExists():
        EC2.start_instances(
            InstanceIds=[getInstanceInfo("instanceId")]
        )
        return True
    else:
        return False

def stopInstance():
    if instanceExists():
        EC2.stop_instances(
            InstanceIds=[getInstanceInfo("instanceId")]
        )
        return True
    else:
        return False

# Checks to see if the minecraft instance is currently running
# Note: if minecraft instance is stopped it will still return true
# It will return false only if the mincraft instance is terimated or does not exist
def instanceExists():
    all_instances = EC2.describe_instances()
    for reservation in all_instances['Reservations']:
        for instance in reservation['Instances']:
            if instance['KeyName'] == KEY_NAME and instance['State']['Code'] != 48:
                return True
    return False

# Usage:
# Minecraft instance must be running first
# 'status' to get minecraft instance running status (ex. running or stopped) - returns string
# 'ipAddress' to get minecraft instance's public ip address - returns address as string
# 'instanceId' to get minecraft's instance id - returns id as string
def getInstanceInfo(info):
    if instanceExists():
        all_instances = EC2.describe_instances()
        for reservation in all_instances['Reservations']:
            for instance in reservation['Instances']:
                if instance['KeyName'] == KEY_NAME and instance['State']['Code'] != 48:
                    if info == "status":
                        return str(instance['State']['Name'])
                    elif info == "statusCode":
                        return instance['State']['Code']
                    elif info == "ipAddress":
                        if instance['State']['Code'] == 16:
                            return str(instance['PublicIpAddress'])
                        else:
                            return "Error. Instance not running"
                    elif info == "instanceId":
                        return str(instance['InstanceId'])

# def describeInstances():
    # print (EC2.describe_instances())