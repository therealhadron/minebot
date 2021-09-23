import sys, os, logging

logger = logging.getLogger("set_server_properties")
logging.basicConfig(level=logging.DEBUG)

from properties_parser import PropertiesParser

def run(properties_path: str):
    RCON_SECRET = os.environ["MC_RCON_SECRET"]
    res = PropertiesParser(properties_path)

    res.set("enable-rcon", "true")
    res.set("rcon.password", RCON_SECRET)
    res.save()
    logger.info(f"Set RCON secret to '{RCON_SECRET}' at '{properties_path}'")

if __name__ == "__main__":
    run(sys.argv[1])
