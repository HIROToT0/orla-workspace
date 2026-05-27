#!/bin/bash
# 深圳招标公告每日抓取任务
# 1. 抓取数据并同步到飞书多维表格
# 2. 发送邮件通知（如有新记录）
# 3. 推送飞书简报（每日必达）

SCRIPT_DIR="/vol1/@apphome/trim.openclaw/data/workspace/szex-bid-notice-sync/scripts"
LOG_FILE="/vol1/@apphome/trim.openclaw/data/workspace/szex-bid-notice-sync/logs/cron.log"

mkdir -p "$(dirname "$LOG_FILE")"

echo "========== $(date '+%Y-%m-%d %H:%M:%S') 开始抓取任务 ==========" >> "$LOG_FILE" 2>&1

# Step 1: 抓取数据并同步到飞书
HOME=/vol1/@apphome/trim.openclaw/data/home
export HOME

python3 "$SCRIPT_DIR/fetch_and_sync.py" >> "$LOG_FILE" 2>&1
FETCH_EXIT=$?

echo "抓取阶段退出码: $FETCH_EXIT" >> "$LOG_FILE" 2>&1

# Step 2: 发送邮件通知（如有新记录）
python3 "$SCRIPT_DIR/send_email.py" >> "$LOG_FILE" 2>&1
EMAIL_EXIT=$?

echo "邮件阶段退出码: $EMAIL_EXIT" >> "$LOG_FILE" 2>&1
echo "========== 任务结束 ==========" >> "$LOG_FILE" 2>&1

# Step 3: 推送飞书简报
python3 "$SCRIPT_DIR/send_feishu.py" >> "$LOG_FILE" 2>&1
FEISHU_EXIT=$?

echo "飞书通知退出码: $FEISHU_EXIT" >> "$LOG_FILE" 2>&1

exit 0
