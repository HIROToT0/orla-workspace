---
name: hermes-agent-docker-deploy
description: Deploy Hermes Agent via three-container Docker Compose setup (hermes gateway + hermes-dashboard + hermes-webui) on a remote Debian host. Triggers when user says "deploy hermes docker", "install hermes agent docker", "hermes 三容器部署", or wants to set up Hermes Agent in Docker on fnOS/Debian.
---

# Hermes Agent Docker Deploy

## Prerequisites

- Remote host: Debian-based, Docker installed, sudo privileges
- SSH access to remote host
- Docker images will be pulled from:
  - `nousresearch/hermes-agent:latest` (~4.94GB)
  - `ghcr.io/nesquena/hermes-webui:latest` (~237MB)

## Deployment Workflow

### 1. SSH Connect & Prepare Directory

```bash
sshpass -p '<password>' ssh -o StrictHostKeyChecking=no <user>@<host>
sudo -S bash -c "mkdir -p <deploy_path>/hermes/data <deploy_path>/hermes/hermes && chown -R 1000:1000 <deploy_path>"
```

Common `<deploy_path>`: `/home/bonbonon/hermes-docker`

### 2. Transfer Files

Transfer to remote host:
- `docker-compose.yml`
- `init.sh`

```bash
sshpass -p '<password>' scp -o StrictHostKeyChecking=no docker-compose.yml init.sh <user>@<host>:<deploy_path>/
```

Then make init.sh executable:
```bash
sshpass -p '<password>' ssh -o StrictHostKeyChecking=no <user>@<host> 'sudo -S chmod +x <deploy_path>/init.sh'
```

### 3. Pull Images

```bash
sudo -S bash -c "cd <deploy_path> && docker compose pull"
```

This takes several minutes due to image sizes. Run in background with `yieldMs` or `background: true`.

### 4. Copy Agent Source (init.sh)

```bash
sudo -S bash -c "cd <deploy_path> && bash init.sh"
```

This copies `/opt/hermes` from the agent image to `<deploy_path>/hermes/hermes/` (required for webui).

### 5. Start Containers

```bash
sudo -S bash -c "cd <deploy_path> && docker compose up -d"
```

Verify:
```bash
sudo -S bash -c "docker ps | grep hermes"
```

Expected output:
| CONTAINER | PORT | STATUS |
|-----------|------|--------|
| hermes | 8642 | Up |
| hermes-dashboard | 9119 | Up |
| hermes-webui | 8787 | Up |

### 6. Configure API Key & Model

The config files are at `<deploy_path>/hermes/data/config.yaml` and `<deploy_path>/hermes/data/.env`.

**MiniMax M2.7 配置（推荐）**

⚠️ 必须同时在 docker-compose.yml 的环境变量和 config.yaml 中配置，缺一不可。

**Step A: 更新 docker-compose.yml（添加环境变量）**

在 hermes 服务的 `environment` 下添加：
```yaml
environment:
  - TZ=Asia/Shanghai
  - FEISHU_APP_ID=cli_xxxxxxxxxxxxx
  - FEISHU_APP_SECRET=xxxxxxxxxxxxxxxx
  - ANTHROPIC_BASE_URL=https://api.minimaxi.com/anthropic
  - ANTHROPIC_AUTH_TOKEN=MINIMAX_API_KEY
  - MINIMAX_API_KEY=sk-cp-你的API密钥
```

然后重启：
```bash
sudo -S bash -c "docker compose down && docker compose up -d"
```

**Step B: 更新 config.yaml**

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

重启使配置生效：
```bash
sudo -S bash -c "docker compose restart hermes"
```

**⚠️ 关键注意事项**

- `ANTHROPIC_AUTH_TOKEN` 必须设为字面值 `MINIMAX_API_KEY`（不是你的实际 key），Hermes 会自动用 `MINIMAX_API_KEY` 环境变量的值替换
- `base_url` 必须是 `https://api.minimaxi.com/v1`（不是 `/anthropic/v1`，那个是错误的）
- 飞书 Bot 的 App ID 和 Secret 也需要在 docker-compose.yml 环境变量中配置
- 飞书开发者后台需要订阅 `im.message.receive_v1` 事件，否则 Bot 收不到消息

**OpenRouter 配置（备选）**

```yaml
model:
  provider: openrouter
  default: anthropic/claude-opus-4.6
  api_key: sk-or-你的OpenRouter密钥

inference:
  provider: openrouter
  base_url: https://openrouter.ai/api/v1
  api_key: sk-or-你的OpenRouter密钥
```

### 7. Set Restart Policy

```bash
sudo -S bash -c "docker update --restart unless-stopped hermes hermes-dashboard hermes-webui"
```

### 8. Configure Messaging Platform (optional)

If connecting to Feishu/Telegram/etc., copy the platform config to `<deploy_path>/hermes/data/platforms/`. Then:
```bash
sudo -S bash -c "docker compose restart hermes"
```

## Key Files Reference

See `references/files.md` for:
- `docker-compose.yml` template
- `init.sh` template
- Config snippet examples
