import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

import os, sys
import json
import requests
import traceback
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "./vendored"))

from core.rcon import send_command

try:
    TOKEN = os.environ['TELEGRAM_TOKEN']
except:
    logger.warning(f"Failed to get telegram token from env, is it set? Error: {traceback.format_exc()}")
    TOKEN = ""

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
        logger.warning(f"Failed to send command to Minecraft. Got error: {traceback.format_exc()}")
        send_telegram_message(chat_id, "Failed to send command, is the server on?")

def send_telegram_message(chat_id: str, message: str):
    url = BASE_URL + "/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message
    }

    res = requests.post(url, data)
    res.raise_for_status()
