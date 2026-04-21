# Hermes Agent Docker Deploy - Reference Files

## docker-compose.yml

```yaml
services:
  hermes:
    image: nousresearch/hermes-agent:latest
    container_name: hermes
    restart: unless-stopped
    command: gateway run
    user: "1000:1000"
    ports:
      - "8642:8642"
    volumes:
      - ./hermes/data:/opt/data
    environment:
      - TZ=Asia/Shanghai
      - FEISHU_APP_ID=cli_xxxxxxxxxxxxx
      - FEISHU_APP_SECRET=xxxxxxxxxxxxxxxx
      - ANTHROPIC_BASE_URL=https://api.minimaxi.com/anthropic
      - ANTHROPIC_AUTH_TOKEN=MINIMAX_API_KEY
      - MINIMAX_API_KEY=sk-cp-你的API密钥
    networks:
      - hermes-net

  dashboard:
    image: nousresearch/hermes-agent:latest
    container_name: hermes-dashboard
    restart: unless-stopped
    command: dashboard --host 0.0.0.0 --insecure
    user: "1000:1000"
    ports:
      - "9119:9119"
    volumes:
      - ./hermes/data:/opt/data
    environment:
      - GATEWAY_HEALTH_URL=http://hermes:8642
      - TZ=Asia/Shanghai
    networks:
      - hermes-net
    depends_on:
      - hermes

  webui:
    image: ghcr.io/nesquena/hermes-webui:latest
    container_name: hermes-webui
    restart: unless-stopped
    ports:
      - "8787:8787"
    volumes:
      - ./hermes/data:/home/hermeswebui/.hermes
      - ./hermes/hermes:/home/hermeswebui/.hermes/hermes-agent
      - ./hermes/data/workspace:/workspace
    environment:
      - HERMES_HOME=/home/hermeswebui/.hermes
      - HERMES_WEBUI_HOST=0.0.0.0
      - HERMES_WEBUI_PORT=8787
      - HERMES_WEBUI_STATE_DIR=/home/hermeswebui/.hermes/webui
      - TZ=Asia/Shanghai
      - WANTED_UID=1000
    networks:
      - hermes-net

networks:
  hermes-net:
    driver: bridge
```

## init.sh

```bash
#!/bin/bash
echo "Copying hermes agent source from image..."
docker run --rm -v $(pwd)/hermes/hermes:/dest nousresearch/hermes-agent:latest cp -r /opt/hermes /dest/
echo "Done. Agent source copied to ./hermes/hermes/"
```

## config.yaml - MiniMax M2.7 Example

```yaml
model:
  provider: minimax
  default: MiniMax-M2.7
  base_url: https://api.minimaxi.com/v1
  key: sk-cp-你的API密钥
  reasoning: true
  extra_body:
    thinking: "on"

inference:
  base_url: https://api.minimaxi.com/v1
  api_key: sk-cp-你的API密钥

gateway:
  platform:
    feishu:
      enabled: true

reasoning:
  effort: high

approvals:
  mode: "off"

FEISHU_HOME_CHANNEL: oc_xxxxxxxxxxxxx
```

## config.yaml - OpenRouter Example

```yaml
model:
  default: "anthropic/claude-opus-4.6"

inference:
  provider: "openrouter"
  base_url: "https://openrouter.ai/api/v1"
  api_key: "sk-or-YOUR-KEY-HERE"
```

## Known Issues & Fixes

### Issue: Permission denied (docker.sock)
Always use `sudo -S bash -c "..."` for docker commands when user lacks direct docker access.

### Issue: hermes-webui shows "No LLM provider configured"
Ensure `HERMES_HOME` env var is set to `/home/hermeswebui/.hermes` in docker-compose.yml.

### Issue: Model changes not taking effect
After updating config.yaml, restart the hermes container:
```bash
sudo -S bash -c "docker compose restart hermes"
```

### Issue: Containers not auto-starting after host reboot
Set restart policy:
```bash
sudo -S bash -c "docker update --restart unless-stopped hermes hermes-dashboard hermes-webui"
```

### Issue: "Unknown provider" or "Connection error" with MiniMax
- `provider` 必须设为 `minimax`（不是 `openai`）
- `ANTHROPIC_BASE_URL` 必须设为 `https://api.minimaxi.com/anthropic`（容器内环境变量）
- `ANTHROPIC_AUTH_TOKEN` 必须设为字面值 `MINIMAX_API_KEY`
- `base_url`（config.yaml）必须设为 `https://api.minimaxi.com/v1`（不是 `/anthropic/v1`）
- 三个环境变量缺一不可：ANTHROPIC_BASE_URL、ANTHROPIC_AUTH_TOKEN、MINIMAX_API_KEY

### Issue: Bot doesn't respond to messages
飞书开发者后台 → Hera App → 事件与回调 → 添加事件订阅：
- `im.message.receive_v1`（收取消息）
添加后需发布新版本 App 才能生效。
