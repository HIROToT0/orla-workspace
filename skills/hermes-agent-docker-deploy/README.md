# hermes-agent-docker-deploy

Hermes Agent 三容器 Docker 部署工具（网关 + 监控面板 + WebUI）。

## 功能

在远程 Debian 主机上通过 Docker Compose 部署 Hermes Agent 三容器架构。

## 包含内容

- `SKILL.md` — 部署流程说明
- `references/files.md` — docker-compose.yml、init.sh、config.yaml 模板
- `hermes-agent-docker-deploy.skill` — 打包文件

## 触发词

「hermes docker 部署」「三容器部署」「deploy hermes」

## 部署端口

| 服务 | 端口 |
|------|------|
| hermes（网关） | 8642 |
| hermes-dashboard | 9119 |
| hermes-webui | 8787 |

## 模型配置（MiniMax M2.7）

⚠️ MiniMax M2.7 配置需要同时修改 docker-compose.yml 环境变量和 config.yaml，缺一不可。

**必需环境变量（docker-compose.yml）：**
```yaml
environment:
  - ANTHROPIC_BASE_URL=https://api.minimaxi.com/anthropic
  - ANTHROPIC_AUTH_TOKEN=MINIMAX_API_KEY
  - MINIMAX_API_KEY=sk-cp-你的API密钥
```

**config.yaml 关键字段：**
```yaml
model:
  provider: minimax
  default: MiniMax-M2.7
  base_url: https://api.minimaxi.com/v1
```

详见 `SKILL.md` Section 6。
