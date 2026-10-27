"""Post to a Discord channel through a webhook (Server settings → Integrations → Webhooks)."""

from __future__ import annotations

import time

import httpx

LIMIT = 2000  # Discord's maximum message length
SUPPRESS_EMBEDS = 1 << 2


def split_message(text: str, limit: int = LIMIT) -> list[str]:
    """Split on line breaks so no message is over Discord's limit."""
    chunks: list[str] = []
    current = ""
    for line in text.split("\n"):
        while len(line) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:limit])
            line = line[limit:]
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) > limit:
            chunks.append(current)
            current = line
        else:
            current = candidate
    if current.strip():
        chunks.append(current)
    return chunks


def post(webhook_url: str, text: str, client: httpx.Client | None = None) -> None:
    client = client or httpx.Client(timeout=20.0)
    for chunk in split_message(text):
        payload = {
            "content": chunk,
            "username": "Price Checker",
            "flags": SUPPRESS_EMBEDS,
            "allowed_mentions": {"parse": []},
        }
        for _ in range(3):
            response = client.post(webhook_url, json=payload)
            if response.status_code == 429:
                time.sleep(float(response.json().get("retry_after", 1)))
                continue
            response.raise_for_status()
            break
        else:
            raise RuntimeError("Discord kept rate limiting the webhook")
