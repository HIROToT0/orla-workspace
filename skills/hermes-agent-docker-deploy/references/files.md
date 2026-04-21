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
  default: "MiniMax-M2.7"

inference:
  provider: "openai"
  base_url: "https://api.minimaxi.chat/v1"
  api_key: "sk-cp-YOUR-KEY-HERE"
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
