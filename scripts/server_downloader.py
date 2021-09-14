import requests

def get_latest_version_url():
    try:
        server_project = "paper"
        server_version = "1.17.1"
        server_build = 259
        base_url = f"https://papermc.io/api/v2/projects/{server_project}/versions/{server_version}\
/builds/{server_build}/downloads/{server_project}-{server_version}-{server_build}.jar"
        r = requests.get(base_url)
        if not r.ok:
            return ""

        return base_url
    except Exception as e:
        print (e)
    return ""