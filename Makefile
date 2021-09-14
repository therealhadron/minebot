MAKEFLAGS += --silent

# Pre-requisites:
# - Java version 16+ For Minecraft servers 1.17.x+ (check with `java -version`)
# - NodeJS (check with `node --version`)
# - Serverless offline plugin
# - It's also recommended that you run this in a python venv to reduce pip clutter

install:
	pip3 install -r requirements.txt
	scripts/fetch_server.sh

local: install
	npm install
	./launch.sh

run: install
	./launch.sh --shutdown

clean:
	rm -rf server
	rm -f server.jar
	rm -rf node_modules

.PHONY: install run clean local
