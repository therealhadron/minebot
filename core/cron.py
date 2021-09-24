import time
import traceback
import signal
import os
from mcstatus import MinecraftServer
from rcon import RCONClient

import logging
logger = logging.getLogger("cron")
logging.basicConfig(level=logging.DEBUG, filename="log.txt")

SECONDS_PER_MINUTE = 60
CHECKS_TO_STOP = 2
STARTUP_WAIT_SECONDS = 2 * SECONDS_PER_MINUTE
CHECK_INTERVAL_SECONDS = 5 * SECONDS_PER_MINUTE

SERVER_HOST = "localhost"
SERVER_PORT = 25565

def stop_server(client: RCONClient):
    try:
        client.save_and_stop()
    except Exception as e:
        logger.warning(f"stop_server() failed, probably because the server is already stopped. There shouldn't be any fatal side effects. Error: {traceback.format_exc()}")

def handle_kill_signal(sig_num, frame):
    logger.info(f"Received stop signal: {sig_num} ({signal.Signals(sig_num).name})")
    raise SystemExit(0)

def get_rcon_secret():
    secret = os.environ.get("MC_RCON_SECRET")
    if secret != None:
        return secret
    
    with open("rcon_secret.txt", "r") as f:
        return f.read()

def main():
    try:
        logger.info("Starting server checker cron...")
        signal.signal(signal.SIGINT, handle_kill_signal)
        signal.signal(signal.SIGTERM, handle_kill_signal)
        num_checks = 0
        logger.info(f"Waiting {STARTUP_WAIT_SECONDS} seconds to let server start up...")
        time.sleep(STARTUP_WAIT_SECONDS)
        logger.info("Checker is now running...")
        RCON_SECRET = get_rcon_secret()
        client = RCONClient(secret=RCON_SECRET)
        server = MinecraftServer(SERVER_HOST, SERVER_PORT)
        while True:
            time.sleep(CHECK_INTERVAL_SECONDS)
            
            # 'status' is supported by all Minecraft servers that are version 1.7 or higher.
            status = server.status()

            if status.players.online > 0:
                num_checks = 0
                logger.info(f"Non-empty server detected with {status.players.online} player(s) online, auto-shutdown reset")
            else:
                num_checks += 1
                logger.warning(f"Empty server detected, auto-shutdown sequence initiated ({num_checks}/{CHECKS_TO_STOP})")
                
            if num_checks >= CHECKS_TO_STOP:
                logger.info("Empty server time exceeded, stopping server...")
                stop_server(client)
                break
    except SystemExit:
        logger.info("Received SystemExit trap, stopping...")
    except Exception:
        logger.error(f"Error occurred while retriving status, stopping cron. Error: {traceback.format_exc()}")
        stop_server()
    finally:
        logger.info("Server stopped, exiting cron")

if __name__ == "__main__":
    main()
