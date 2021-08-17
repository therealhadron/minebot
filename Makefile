MAKEFLAGS += --silent

install:
	pip install -r requirements.txt
	scripts/fetch_server.sh

run: install
	cd core && python3 cron.py &
	scripts/init_server_settings.sh && cd server && java -Xmx1024M -Xms1024M -jar ../server.jar nogui

clean:
	rm -rf server
	rm -f server.jar

.PHONY: install run clean
