import requests

def get_latest_version_url():
    try:
        manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
        r = requests.get(manifest_url)
        if not r.ok:
            return ""

        versions_url = r.json()["versions"][0]["url"]

        r = requests.get(versions_url)
        if not r.ok:
            return ""
    
        server_jar_url = r.json()["downloads"]["server"]["url"]
        
        return server_jar_url

    except Exception as e:
        print(e)
    
    return ""
