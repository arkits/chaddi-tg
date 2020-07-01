#!/usr/bin/env bash

function check_config() {
	if [ ! -f /bot/resources/config.json ]; then
		if [[ -z "$BOT_USERNAME" ]]; then
			echo "BOT_USERNAME not set"
			exit 1
		fi

		if [[ -z "$TG_TOKEN" ]]; then
			echo "TG_TOKEN not set"
			exit 1
		fi

		if [[ -z "$GM_CHANNELS" ]]; then
			export GM_CHANNELS=[]
		fi

		if [[ -z "$HI_RESPONSE" ]]; then
			export HI_RESPONSE=[]
		fi

		if [[ "$ENABLE_WEBHOOK:0" -eq 0 ]]; then
			export ENABLE_WEBHOOK=0
		else
			export ENABLE_WEBHOOK=1
			if [[ -z "$WEBHOOK_URL" ]]; then
				echo "ENABLE_WEBHOOK is set but no webhook url is specified"
				exit 1
			fi
		fi

		envsubst '${BOT_USERNAME}
		${TG_TOKEN}
		${GM_CHANNELS}
		${HI_RESPONSE}
		${ENABLE_WEBHOOK}' < /bot/resources/config.json.template > /bot/resources/config.json
	fi
}

check_config
exec "$a"
