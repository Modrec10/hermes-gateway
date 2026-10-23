#!/bin/bash
set -euo pipefail
mkdir -p /root/.hermes/profiles/jailbreak
echo "==> fetching profile bundle"
curl -fsSL -H "Authorization: Bearer ${HF_TOKEN}" \
  "https://huggingface.co/datasets/LukaLZ/hermes-profile-store/resolve/main/profile.tar.gz" \
  -o /tmp/profile.tar.gz
echo "==> bundle size: $(stat -c%s /tmp/profile.tar.gz) bytes"
tar -xzf /tmp/profile.tar.gz -C /root/.hermes/profiles/jailbreak
echo "==> profile extracted: $(ls /root/.hermes/profiles/jailbreak | wc -l) entries"

# PC-bridge relay on the public port (health + /ws/agent + /run)
python3 /app/relay.py &

exec hermes --profile jailbreak gateway run
