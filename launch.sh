#!/bin/bash
# This script launches the minecraft server along with its cron job

kill_child_processes() {
    echo "Server stopped, stopping cron child process"
    kill -TERM ${cron} 2> /dev/null
}

# Kill child processes on SIGINT or SIGTERM
trap kill_child_processes SIGINT SIGTERM

# Start background cron job
python3 core/cron.py &
cron=$!

# Start MC server
scripts/init_server_settings.sh && cd server && java -Xmx512M -Xms512M -jar ../server.jar nogui

# Kill child processes when server stops gracefuly
# Whether if the server stops gracefully or killed, stop child processes
kill_child_processes
