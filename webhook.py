import boto3
from botocore.credentials import create_assume_role_refresher
from botocore.exceptions import ClientError # todo add error handling and loggimg to code

import logging
logger = logging.getLogger("webhook")
logging.basicConfig(level=logging.DEBUG)

import os
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
NO_IP_USER = os.environ['NO_IP_USER']
NO_IP_PASSWORD = os.environ['NO_IP_PASSWORD']
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
        elif message == "/start":
            send_telegram_message(chat_id, "Welcome to minebot!\n\nUse /help to see what I can do!")
        elif message == "/help":
            send_telegram_message(chat_id,
            '''/help - Brings up this help menu
        /startInstance - Starts/creates the minecraft ec2 instance and turns on the minecraft server
        /stopInstance - Stops the minecraft ec2 instance and turns off the minecraft server
        /getInstanceStatus - Gets the current status of the instance (pending, stopping, stopped, etc.)
        /getInstanceIpAddress - Gets the public ip address of the instance in case you are having trouble connecting to No-Ip
            ''')
        elif message == "/startInstance":
            if instance == None:
                if key_pair_exists() and security_group_exists():
                    if create_instance():
                        send_telegram_message(chat_id, "Successfully created and started instance!")
                    else:
                        send_telegram_message(chat_id, "Error creating instance")
                else:
                    send_telegram_message(chat_id, "key pair or security group does not exist creating them now...")
                    if create_key_pair():
                        send_telegram_message(chat_id, "Successfully created new key pair")
                    else:
                        send_telegram_message(chat_id, "Error creating key pair")
                    if create_security_group():
                        send_telegram_message(chat_id, "Successfully created new security group")
                    else:
                        send_telegram_message(chat_id, "Error creating security group")
                    send_telegram_message(chat_id, "Please run 'startInstance' again")
            else:
                if instance.state['Code'] == InstanceState.running:
                    send_telegram_message(chat_id, "Instance already running!")
                elif instance.state['Code'] == InstanceState.stopped:
                    start_instance(instance)
                    send_telegram_message(chat_id, "Starting instance")
                else:
                    send_telegram_message(chat_id, f"Instance already exists it is currently: {instance.state['Name']}")
        elif message == "/createKeyPair":
            create_key_pair()
            send_telegram_message(chat_id, "Successfully created new key pair")
        elif message == "/createSecurityGroup":
            if security_group_exists():
                send_telegram_message(chat_id, "Security group exists")
            else:
                create_security_group()
                send_telegram_message(chat_id, "Successfully created new security group")
        elif message == "/getInstanceStatus":
            if instance != None:
                send_telegram_message(chat_id, f"The instance is currently: {instance.state['Name']}")
            else:
                send_telegram_message(chat_id, "No instance exist. Start a new one first")
        elif message == "/getInstanceIpAddress":
            if instance != None and instance.state['Code'] == InstanceState.running:
                send_telegram_message(chat_id, f"Instance Ip Address is: {instance.public_ip_address}")
            else:
                send_telegram_message(chat_id, "No instance exist or instance is not running. Start a new/start instance first")
        elif message == "/stopInstance":
            if instance == None:
                send_telegram_message(chat_id, "Instance does not exist! Nothing to stop!")
            else:
                if instance.state['Code'] == InstanceState.running:
                    stop_instance(instance)
                    send_telegram_message(chat_id, "Instance stopping")
                else:
                    send_telegram_message(chat_id, f"Instance is currently {instance.state['Code']}")
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

# return true if key pair creation is successful
# return false if key pair creation fails
def create_key_pair():
    try:
        ec2.create_key_pair(KeyName = KEY_NAME)
        return True
    except:
        # to do add error logging
        return False

def key_pair_exists():
    key_pairs = ec2.key_pairs.all()
    for key in key_pairs:
        if key.key_name == KEY_NAME:
            return True
    return False

# return true if create securtiy group is successful
# return false if create security group fails
def create_security_group():
    try:
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
                        # for rcon
                        'IpProtocol': 'tcp',
                        'FromPort': 25575,
                        'ToPort': 25575,
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
        return True
    except:
        # to do add error logging
        return False

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

# Return true if creating instance without errors
# Return false if fails
def create_instance():
    try:
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
            SecurityGroups = [SECURITY_GROUP_NAME],
            UserData = f'''#! /bin/bash\n

                            echo "Updating OS"\n
                            yum -y update\n

                            echo "Installing noip client"\n
                            yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm\n
                            yum install -y noip\n
                            noip2 -C -U 30 -u {NO_IP_USER} -p {NO_IP_PASSWORD}\n
                            systemctl enable noip.service\n
                            systemctl start noip.service\n

                            echo "Installing Java 16"\n
                            yum install -y wget\n
                            wget --no-check-certificate -c --header "Cookie: oraclelicense=accept-securebackup-cookie" https://download.oracle.com/otn-pub/java/jdk/16.0.2%2B7/d4a915d82b4c4fbb9bde534da945d746/jdk-16.0.2_linux-x64_bin.rpm\n
                            rpm -ivh jdk-16.0.2_linux-x64_bin.rpm\n

                            echo "Downloading and creating scripts from GitHub..."\n

                            yum install -y git\n
                            git clone https://github.com/Cypheruim/minebot.git\n

                            cp /minebot/minebot-startup.service /etc/systemd/system/\n
                            chmod +x /minebot/start.sh\n
                            systemctl enable minebot-startup.service\n
                            systemctl start minebot-startup.service\n
                            '''
        )
        return True
    except:
        return False

# to do
# check if instance start is successful
def start_instance(instance):
    instance.start()

# to do
# check if instance stop is successful
def stop_instance(instance):
    instance.stop()

# Finds the minecraft instance and returns it if found
# Otherwise return none
def load_instance():
    all_instances = ec2.instances.all()
    for instance in all_instances:
        if instance.key_name == KEY_NAME and instance.state['Code'] != InstanceState.terminated:
            return instance
    return None