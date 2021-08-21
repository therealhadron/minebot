from mcrcon import MCRcon
import time

HOST = "localhost"
SECRET = "69420"

def save_and_stop(wait_time_seconds = None):
    with MCRcon(HOST, SECRET) as mcr:
        if wait_time_seconds:
            mcr.command(f"/tellraw @a {{\"text\":\"Server shutting down in {wait_time_seconds} seconds\",\"color\":\"#ff0000\"}}")
            time.sleep(wait_time_seconds)
        mcr.command('save-all')
        mcr.command('stop')


def send_command(command: str):
    with MCRcon(HOST, SECRET) as mcr:
        return mcr.command(command)
