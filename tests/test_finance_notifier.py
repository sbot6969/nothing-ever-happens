from __future__ import annotations

from unittest.mock import patch

from bot import finance_notifier


def test_finance_notifier_prefers_direct_telegram_bot(monkeypatch):
    monkeypatch.setenv("FINANCE_TG_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("FINANCE_TG_CHAT_ID", "-10042")
    monkeypatch.setenv("FINANCE_TG_TARGET", "")
    with patch("bot.finance_notifier.urllib.request.urlopen") as urlopen, patch("bot.finance_notifier.subprocess.run") as run:
        urlopen.return_value.__enter__.return_value.read.return_value = b"{}"
        finance_notifier._send_message("hello")
    assert urlopen.called
    assert not run.called


def test_finance_notifier_falls_back_to_openclaw_without_bot_token(monkeypatch):
    monkeypatch.delenv("FINANCE_TG_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TG_BOT_TOKEN", raising=False)
    monkeypatch.setenv("FINANCE_TG_TARGET", "@target")
    with patch("bot.finance_notifier.subprocess.run") as run:
        finance_notifier._send_message("hello")
    assert run.called


def test_has_destination_accepts_token_and_chat_id_without_target(monkeypatch):
    monkeypatch.setenv("FINANCE_TG_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("FINANCE_TG_CHAT_ID", "-10042")
    monkeypatch.setenv("FINANCE_TG_TARGET", "")
    assert finance_notifier._has_destination()
