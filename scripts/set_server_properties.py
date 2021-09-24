import sys, os, logging, traceback

logger = logging.getLogger("set_server_properties")
logging.basicConfig(level=logging.DEBUG, filename="log.txt")

from properties_parser import PropertiesParser

def run(properties_path: str):
    RCON_SECRET = os.environ["MC_RCON_SECRET"]
    with PropertiesParser(properties_path) as props:
        props.set("enable-rcon", "true")
        props.set("rcon.password", RCON_SECRET)

    logger.info(f"Successfully set RCON to '{RCON_SECRET}' at '{properties_path}'")

if __name__ == "__main__":
    try:
        run(sys.argv[1])
    except:
        logger.error(f"Failed to set server properties: {traceback.format_exc()}")
