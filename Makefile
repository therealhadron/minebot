MAKEFLAGS += --silent

install:
	pip install -r requirements.txt
	scripts/fetch_server.sh

run: install
	cd core && python3 cron.py &
	mkdir -p server && cd server && java -Xmx1024M -Xms1024M -jar ../server.jar nogui

clean:
	rm -rf server
	rm server.jar 2> /dev/null

.PHONY: install run clean
