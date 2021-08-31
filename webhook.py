import boto3
from botocore.exceptions import ClientError
import logging
logger = logging.getLogger("webhook")
logging.basicConfig(level=logging.DEBUG)
import os, sys
import json
import requests
import traceback
from enum import IntEnum

from core.rcon import send_command

try:
    TOKEN = os.environ['TELEGRAM_TOKEN']
except:
    logger.error(f"Failed to get telegram token from env, is it set? Error: {traceback.format_exc()}")
    TOKEN = ""

ec2 = boto3.resource('ec2')

KEY_NAME = 'minebot_server_key'
SECURITY_GROUP_NAME = 'minebot_security'

TOKEN = os.environ['TELEGRAM_TOKEN']
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

class InstanceState(IntEnum):
    pending = 0
    running = 16
    shutting_down = 32
    terminated = 48
    stopping = 64
    stopped = 80

def handler(event, context):
    try:
        data = event["body"]
        message = str(data["message"]["text"])
        chat_id = data["message"]["chat"]["id"]

        logger.info(f"Received message: {message}")
        command_prefix = "/cmd"
        instance = load_instance()

        if message.startswith(command_prefix):
            _send_minecraft_command(chat_id, message[len(command_prefix):])
        elif message.startswith("/start_server"):
            _start_minecraft_server(chat_id)
        elif message.startswith("/stop_server"):
            _send_minecraft_command(chat_id, "stop")
        elif message == "startInstance":
            if instance == None:
                if key_pair_exists() and security_group_exists():
                    create_instance()
                    send_telegram_message(chat_id, "Successfully created and started instance!")
                else:
                    send_telegram_message(chat_id, "key pair or security group does not exist creating them now...")
                    if not key_pair_exists():
                        create_key_pair()
                        send_telegram_message(chat_id, "Successfully created new key pair")
                    if not security_group_exists():
                        create_security_group()
                        send_telegram_message(chat_id, "Successfully created new security group")
                    send_telegram_message(chat_id, "Please run 'startInstance' again")
            else:
                if instance.state['Code'] == InstanceState.running:
                    send_telegram_message(chat_id, "Instance already running!")
                elif instance.state['Code'] == InstanceState.stopped:
                    start_instance(instance)
                    send_telegram_message(chat_id, "Starting instance")
                else:
                    send_telegram_message(chat_id, f"Instance already exists is it is currently: {instance.state['Name']}")
        elif message == "createKeyPair":
            create_key_pair()
            send_telegram_message(chat_id, "Successfully created new key pair")
        elif message == "createSecurityGroup":
            if security_group_exists():
                send_telegram_message(chat_id, "Security group exists")
            else:
                create_security_group()
                send_telegram_message(chat_id, "Successfully created new security group")
        elif message == "getInstanceStatus":
            if instance != None:
                send_telegram_message(chat_id, f"The instance is currently: {instance.state['Name']}")
            else:
                send_telegram_message(chat_id, "No instance exist. Start a new one first")
        elif message == "getInstanceIpAddress":
            if instance != None and instance.state['Code'] == InstanceState.running:
                send_telegram_message(chat_id, f"Instance Ip Address is: {instance.public_ip_address}")
            else:
                send_telegram_message(chat_id, "No instance exist or instance is not running. Start a new/start instance first")
        elif message == "stopInstance":
            send_telegram_message(chat_id, "Instance stopping")
        else:
            send_telegram_message(chat_id, f"Command not recognized: '{message}'")
    except Exception as e:
        logger.error(f"Request failed with error: {traceback.format_exc()}")

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

def create_key_pair():
    if not key_pair_exists():
        ec2.create_key_pair(KeyName = KEY_NAME)

def key_pair_exists():
    key_pairs = ec2.key_pairs.all()
    for key in key_pairs:
        if key.key_name == KEY_NAME:
            return True
    return False

def create_security_group():
    security_group = ec2.create_security_group(
        GroupName = SECURITY_GROUP_NAME,
        Description = f"{SECURITY_GROUP_NAME}_group",
        VpcId = str(get_vpc())
    )
    security_group.authorize_ingress(
        GroupName=security_group.group_name,
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

def security_group_exists():
    security_groups = ec2.security_groups.all()
    for group in security_groups:
        if group.group_name == SECURITY_GROUP_NAME:
            return True
    return False

def get_vpc():
    security_groups = ec2.security_groups.all()
    for group in security_groups:
        if group.group_name == 'default':
            return group.vpc_id

def create_instance():
    ec2.create_instances(
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

# to do
# check if instance start is successful
def start_instance(instance):
    instance.start()

# to do
# check if instance stop is successful
def stop_instance(instance):
    instance.stop()

# Usage:
# Minecraft instance must be running first
# 'status' to get minecraft instance running status (ex. running or stopped) - returns string
# 'ipAddress' to get minecraft instance's public ip address - returns address as string
# 'instanceId' to get minecraft's instance id - returns id as string
def get_instance_info(info, instance):
    if info == "status":
        return str(instance.state['Name'])
    elif info == "statusCode":
        return instance.state['Code']
    elif info == "ipAddress":
        if instance.state['Code'] == InstanceState.running:
            return str(instance.public_ip_address)
        else:
            return "Error. Instance not running"
    elif info == "instanceId":
        return str(instance.instance_id)
    return None

# Finds the minecraft instance and returns it if found
# Otherwise return none
def load_instance():
    all_instances = ec2.instances.all()
    for instance in all_instances:
        if instance.key_name == KEY_NAME and instance.state['Code'] != InstanceState.terminated:
            return instance
    return None