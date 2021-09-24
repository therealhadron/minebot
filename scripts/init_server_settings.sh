# Sets up the minecraft server configs if not already setup
EULA_FILE=eula.txt
PROPERTIES_FILE=server.properties
LOG_FILE=log.txt

mkdir -p server

if [ ! -f server/$EULA_FILE ]; then
    echo "Creating an agreed EULA file..." >> $LOG_FILE
    cp templates/${EULA_FILE} server
fi

if [ ! -f server/$PROPERTIES_FILE ]; then
    echo "Creating a RCON-enabled server.properties file..." >> $LOG_FILE
    cp templates/${PROPERTIES_FILE} server
    echo "Setting the RCON secret..." >> $LOG_FILE
    python3 scripts/set_server_properties.py server/$PROPERTIES_FILE
fi
