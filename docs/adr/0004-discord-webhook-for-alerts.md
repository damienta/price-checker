# 0004. Send alerts through a Discord webhook

- **Status:** Accepted
- **Date:** 2026-10-27

## Context

Alerts need to reach a phone, for free, without installing anything new or building a bot.

## Options considered

- **WhatsApp Business API**: needs Meta business setup, charges per message outside the 24-hour
  window, and Meta restricts general-purpose AI bots. Unofficial libraries risk a ban.
- **Telegram bot**: free and simple, but means installing Telegram.
- **Email**: no install, but easy to ignore and needs SMTP credentials.
- **Discord webhook**: just a URL, no bot code or hosting, free, and Discord is already installed.

## Decision

One webhook URL, stored as the `DISCORD_WEBHOOK_URL` secret. `discord.py` splits messages at
Discord's 2,000-character limit, turns off link previews and @mentions, and retries when rate
limited.

## Consequences

- A webhook can only post. To add items by Discord command (e.g. `/track`), we'd need a proper
  Discord bot with somewhere to run it.
- Sending is one function, so adding email or push notifications later is a new module plus a
  setting, not a rewrite.

**Revisit when:** other users join (each needs their own channel, or a bot that DMs them), or
when replying to alerts is wanted.
