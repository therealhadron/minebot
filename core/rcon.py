from dataclasses import dataclass
from mcrcon import MCRcon
import time

HOST = "localhost"

@dataclass
class RCONClient:
    host: str
    secret: str

    def __init__(self, host=HOST, secret=""):
        self.host = host
        self.secret = secret

    def save_and_stop(self, wait_time_seconds = None):
        with MCRcon(self.host, self.secret) as mcr:
            if wait_time_seconds:
                mcr.command(f"/tellraw @a {{\"text\":\"Server shutting down in {wait_time_seconds} seconds\",\"color\":\"#ff0000\"}}")
                time.sleep(wait_time_seconds)
            mcr.command('save-all')
            mcr.command('stop')

    def send_command(self, command: str):
        with MCRcon(self.host, self.secret) as mcr:
            return mcr.command(command)
