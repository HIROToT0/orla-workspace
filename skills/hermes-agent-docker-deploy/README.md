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
