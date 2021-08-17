import time, logging
from mcstatus import MinecraftServer
from rcon import save_and_stop

SECONDS_PER_MINUTE = 60
CHECKS_TO_STOP = 2
STARTUP_WAIT_SECONDS = 2 * SECONDS_PER_MINUTE
CHECK_INTERVAL_SECONDS = 5 * SECONDS_PER_MINUTE

SERVER_HOST = "localhost"
SERVER_PORT = 25565

def stop_server():
    try:
        save_and_stop()
    except Exception as e:
        logging.warning(f"stop_server() failed, but it shouldn't have any side effects. Error: {e}")

def main():
    logging.warning("Starting server checker cron...")
    num_checks = 0
    logging.warning(f"Waiting {STARTUP_WAIT_SECONDS} seconds to let server start up...")
    time.sleep(STARTUP_WAIT_SECONDS)

    try:
        logging.warning(f"Checker is now running...")
        server = MinecraftServer(SERVER_HOST, SERVER_PORT)
        while True:
            time.sleep(CHECK_INTERVAL_SECONDS)
            
            # 'status' is supported by all Minecraft servers that are version 1.7 or higher.
            status = server.status()

            if status.players.online > 0:
                num_checks = 0
                logging.warning(f"Non-empty server detected with {status.players.online} player(s) online, auto-shutdown reset")
            else:
                num_checks += 1
                logging.warning(f"Empty server detected, auto-shutdown sequence initiated ({num_checks}/{CHECKS_TO_STOP})")
                
            if num_checks > CHECKS_TO_STOP:
                logging.warning("Empty server time exceeded, stopping server...")
                stop_server()
                break

    except Exception as e:
        logging.error(f"Error occurred while retriving status, stopping cron. Error: {e}")
        stop_server()
    finally:
        logging.warning("Server stopped, exiting cron")

if __name__ == "__main__":
    main()
