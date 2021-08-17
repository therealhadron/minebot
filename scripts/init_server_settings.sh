# Sets up the minecraft server configs if not already setup
EULA_FILE=eula.txt
PROPERTIES_FILE=server.properties

mkdir -p server

if [ ! -f server/$EULA_FILE ]; then
    echo "Creating an agreed EULA file..."
    cp templates/${EULA_FILE} server
fi


if [ ! -f server/$PROPERTIES_FILE ]; then
    echo "Creating a RCON-enabled server.properties file..."
    cp templates/${PROPERTIES_FILE} server
fi
