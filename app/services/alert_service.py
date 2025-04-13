from discord_webhook import DiscordWebhook, DiscordEmbed
import os
from enum import Enum

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


class AlertType(Enum):
    INFO = "03b2f8"
    WARNING = "ffff00"
    ERROR = "ff0000"
    SUCCESS = "00ff00"
    DEBUG = "0000ff"
    ORANGE = "ffa500"


def get_webhook():
    if not DISCORD_WEBHOOK_URL:
        return None
    return DiscordWebhook(url=DISCORD_WEBHOOK_URL)


def send_alert(name: str, message: str, type: AlertType):
    webhook = get_webhook()
    if not webhook:
        return
    embed = DiscordEmbed(title=name, description=message, color=type.value)
    webhook.add_embed(embed)
    webhook.execute()
