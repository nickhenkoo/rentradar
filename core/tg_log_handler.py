"""
Logging handler that sends WARNING+ records to a Telegram channel.
Uses a background thread per-message so the async event loop is never blocked.
"""
import logging
import threading

import httpx

_LEVEL_EMOJI = {
    logging.WARNING:  "⚠️",
    logging.ERROR:    "🔴",
    logging.CRITICAL: "🚨",
}

_SEND_TIMEOUT = 5  # seconds


class TelegramLogHandler(logging.Handler):
    def __init__(self, token: str, channel_id: str) -> None:
        super().__init__(level=logging.WARNING)
        self._url = f"https://api.telegram.org/bot{token}/sendMessage"
        self._channel_id = channel_id

    def emit(self, record: logging.LogRecord) -> None:
        try:
            text = self._format(record)
            threading.Thread(target=self._send, args=(text,), daemon=True).start()
        except Exception:
            pass

    def _format(self, record: logging.LogRecord) -> str:
        emoji = _LEVEL_EMOJI.get(record.levelno, "ℹ️")
        level = record.levelname
        name = record.name
        msg = record.getMessage()
        if record.exc_info:
            import traceback
            msg += "\n" + "".join(traceback.format_exception(*record.exc_info))
        # Telegram message limit: 4096 chars; leave room for header
        body = msg[:3800]
        return f"{emoji} <b>[{level}]</b> <code>{name}</code>\n<pre>{_escape(body)}</pre>"

    def _send(self, text: str) -> None:
        try:
            httpx.post(
                self._url,
                json={"chat_id": self._channel_id, "text": text, "parse_mode": "HTML"},
                timeout=_SEND_TIMEOUT,
            )
        except Exception:
            pass  # never raise from a log handler


def _escape(text: str) -> str:
    """Minimal HTML escaping for <pre> blocks."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
