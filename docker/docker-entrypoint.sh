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
			export GM_CHANNELS=()
		fi

		if [[ -z "$HI_RESPONSE" ]]; then
			export HI_RESPONSE=()
		fi

		if [[ "$ENABLE_WEBHOOK" -eq 0 ]]; then
			export ENABLE_WEBHOOK=0
		else
			export ENABLE_WEBHOOK=1
			if [[ -z "$WEBHOOK_URL" ]]; then
				echo "ENABLE_WEBHOOK is set but no webhook url is specified"
				exit 1
			fi
		fi

		declare -a GM_CHANNELS="$GM_CHANNELS"
		declare -a HI_RESPONSE="$HI_RESPONSE"

		read -r -d '' configuration << EOF
{"bot_username": "${BOT_USERNAME}",
"tg_bot_token": "${TG_TOKEN}",
"good_morning_channels": $(printf "%s\n" "${GM_CHANNELS[@]}" | jq -R . | jq -s .),
"hi_response_whitelist": $(printf "%s\n" ${HI_RESPONSE[@]} | jq -R . | jq -s .),
"webhook": {"enabled": ${ENABLE_WEBHOOK}, "url": "${WEBHOOK_URL}"}}
EOF
		echo "$configuration" | jq . > /bot/resources/config.json
	fi
}

check_config
python -m nltk.downloader stopwords
exec "$@"
