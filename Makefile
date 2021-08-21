MAKEFLAGS += --silent

# Pre-requisites:
# - Java version 16+ For Minecraft servers 1.17.x+ (check with `java -version`)
# - NodeJS (check with `node --version`)
# - Serverless offline plugin
# - It's also recommended that you run this in a python venv to reduce pip clutter

install:
	pip install -r requirements.txt
	npm install
	scripts/fetch_server.sh

run: install
	cd core && python3 cron.py &
	scripts/init_server_settings.sh && cd server && java -Xmx1024M -Xms1024M -jar ../server.jar nogui

clean:
	rm -rf server
	rm -f server.jar
	rm -rf node_modules

.PHONY: install run clean
