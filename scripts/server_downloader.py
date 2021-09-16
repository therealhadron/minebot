import traceback
import logging
logger = logging.getLogger("server_downloader")
logging.basicConfig(level=logging.DEBUG)

def get_latest_version_url():
    try:
        server_project = "paper"
        server_version = "1.17.1"
        server_build = 259
        base_url = f"https://papermc.io/api/v2/projects/{server_project}/versions/{server_version}\
/builds/{server_build}/downloads/{server_project}-{server_version}-{server_build}.jar"

        return base_url
    except Exception:
        logger.error(f"get_latest_version_url failed with error: {traceback.format_exc()}")
    return ""
