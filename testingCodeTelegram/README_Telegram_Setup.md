# Telegram Notifications Setup

## Step 1 — Create a bot
- Open Telegram and start chat with **@BotFather**
- Send `/newbot` and follow prompts
- Save the **BOT TOKEN**
- Optional: `/setprivacy` → choose your bot → **Disable**

## Step 2 — Add bot to your group
- Open your group → Add members → add your bot

## Step 3 — Find CHAT_ID
- Send any message in the group
- Open: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
- Find `chat.id` (group id is usually negative), copy it as `TELEGRAM_CHAT_ID`

## Step 4 — Configure backend/.env
```
NOTIFY_TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_CHAT_ID=-100xxxxxxxxxx
```

## Test
- Start backend, then call `GET /admin/telegram/test`
- You should receive a test message in your group
