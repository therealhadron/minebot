#!/bin/bash
# This script launches the minecraft server along with its background cron job
# When terminated, it will shut down the system (if specified)

# Stops the cron job child process
kill_child_processes() {
    echo "Server stopped, stopping cron child process"
    kill -TERM ${cron} 2> /dev/null
}

# Shuts down the instance
# Note: shutting down will STOP in the instance, not TERMINATE
shutdown_instance() {
    echo "Shutting system down..."
    # Wait for a few seconds before shutting down in case clean up scripts are still running
    # shutdown command cannot specify lengths under a minute so use sleep instead
    sleep 10
    # shutdown now
}

# Kills any child processes and shut down the system if the shutdown flag is specified
clean_up() {
    kill_child_processes
    if [ "$1" = "--shutdown" ]; then
        shutdown_instance
    fi
}

# Run clean up when server stops (gracefully or killed)
trap 'clean_up $1' EXIT

# Start background cron job
python3 core/cron.py &
cron=$!

# Start MC server
scripts/init_server_settings.sh && cd server && java -Xms512M -Xmx1024M -jar ../server.jar nogui