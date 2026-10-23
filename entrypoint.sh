#!/bin/bash
set -e
mkdir -p /root/.hermes/profiles/jailbreak
curl -sL -H "Authorization: Bearer ${HF_TOKEN}" \
  "https://huggingface.co/datasets/LukaLZ/hermes-profile-store/resolve/main/profile.tar.gz" \
  -o /tmp/profile.tar.gz
tar -xzf /tmp/profile.tar.gz -C /root/.hermes/profiles/jailbreak

# Render requires an HTTP listener on $PORT; Hermes gateway is outbound-only,
# so a tiny health server answers Render's (and UptimeRobot's) pings.
python3 -m http.server "${PORT:-10000}" --bind 0.0.0.0 --directory /app &

exec hermes --profile jailbreak gateway run
