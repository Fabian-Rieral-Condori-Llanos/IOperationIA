import os

import requests

from config import TELEGRAM_API_BASE_URL, TELEGRAM_TIMEOUT_SECONDS


class TelegramClient:
    def __init__(self, token):
        self.token = token

    @property
    def enabled(self):
        return bool(self.token)

    def _url(self, method):
        return f"{TELEGRAM_API_BASE_URL}/bot{self.token}/{method}"

    def send_message(self, chat_id, text):
        if not self.enabled:
            raise RuntimeError("TELEGRAM_BOT_TOKEN no esta configurado")
        if not chat_id:
            raise ValueError("No existe chat_id de Telegram para enviar la notificacion")

        response = requests.post(
            self._url("sendMessage"),
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=TELEGRAM_TIMEOUT_SECONDS,
        )
        self._raise_for_telegram(response)
        return response.json()

    def get_updates(self, offset=None, timeout=0):
        if not self.enabled:
            raise RuntimeError("TELEGRAM_BOT_TOKEN no esta configurado")

        params = {"timeout": timeout, "allowed_updates": ["message"]}
        if offset is not None:
            params["offset"] = offset

        response = requests.get(
            self._url("getUpdates"),
            params=params,
            timeout=TELEGRAM_TIMEOUT_SECONDS + int(timeout or 0),
        )
        self._raise_for_telegram(response)
        return response.json().get("result", [])

    def send_document(self, chat_id, document, caption=None):
        if not self.enabled:
            raise RuntimeError("TELEGRAM_BOT_TOKEN no esta configurado")
        if not chat_id:
            raise ValueError("No existe chat_id de Telegram para enviar el documento")

        data = {"chat_id": chat_id}
        if caption:
            data["caption"] = caption
            data["parse_mode"] = "HTML"

        if self._is_url(document):
            response = requests.post(
                self._url("sendDocument"),
                data={**data, "document": document},
                timeout=TELEGRAM_TIMEOUT_SECONDS,
            )
        else:
            if not os.path.exists(document):
                raise FileNotFoundError(f"No existe el PDF de factura: {document}")
            with open(document, "rb") as pdf_file:
                response = requests.post(
                    self._url("sendDocument"),
                    data=data,
                    files={"document": pdf_file},
                    timeout=TELEGRAM_TIMEOUT_SECONDS,
                )

        self._raise_for_telegram(response)
        return response.json()

    @staticmethod
    def _is_url(value):
        value = str(value or "")
        return value.startswith("http://") or value.startswith("https://")

    @staticmethod
    def _raise_for_telegram(response):
        if response.ok:
            payload = response.json()
            if payload.get("ok"):
                return
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        raise RuntimeError(f"Telegram rechazo la solicitud: {detail}")
