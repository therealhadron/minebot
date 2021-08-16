import json
import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "./vendored"))
import requests

TOKEN = os.environ['TELEGRAM_TOKEN']
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

def handler(event, context):
    data = json.loads(event["body"])
    message = str(data["message"]["text"])
    chat_id = data["message"]["chat"]["id"]

    url = BASE_URL + "/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message
    }

    res = requests.post(url, data)
    res.raise_for_status()
    return {"statusCode":200}