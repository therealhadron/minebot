# Downloads the minecraft server jar file if it doesn't exist
# currently just 1.17.1 hard-coded
SERVER_FILE=server.jar
SERVER_FILE_URL=https://launcher.mojang.com/v1/objects/a16d67e5807f57fc4e550299cf20226194497dc2/server.jar

if [ ! -f $SERVER_FILE ]; then
    echo "Server file not found, fetching from Mojang..."
    curl $SERVER_FILE_URL --output $SERVER_FILE
fi
