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

**Option A: OpenAI-compatible endpoint (e.g. MiniMax)**

In `config.yaml`, set:
```yaml
model:
  default: "MiniMax-M2.7"

inference:
  provider: "openai"  # or "custom" for base_url override
  base_url: "https://api.minimaxi.chat/v1"
  api_key: "sk-cp-..."  # your API key
```

Also set in `.env`:
```
OPENAI_API_KEY=sk-cp-xxx
```

Then restart:
```bash
sudo -S bash -c "docker compose restart hermes"
```

**Option B: OpenRouter**
```yaml
inference:
  provider: "openrouter"
  base_url: "https://openrouter.ai/api/v1"
  api_key: "sk-or-..."  # your OpenRouter key
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
