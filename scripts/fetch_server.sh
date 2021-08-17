# Downloads the minecraft server jar file if it doesn't exist
# currently just 1.17.1 hard-coded
SERVER_FILE=server.jar
SERVER_FILE_URL=$(python -c 'from scripts.server_downloader import get_latest_version_url; print(get_latest_version_url())')

if [ ! -f $SERVER_FILE ]; then
    echo "Server file not found, downloading from Mojang..."
    curl $SERVER_FILE_URL --output $SERVER_FILE
fi
