import asyncio
import logging
import discord
from discord.ext import commands

from src.utils.config_loader import ConfigLoader
from src.infra.cron_http import start_http_server

# ⬇️ NEW: import chat manager and adapter
from src.services.chat_manager import ChatManager
from src.adapters.chat.discord_client import DiscordChatClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def create_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True
    return commands.Bot(command_prefix="!", intents=intents)

async def main():
    # --- Load configuration ---
    config = ConfigLoader()
    token = config.get_discord_token()

    # --- Initialize the bot ---
    bot = create_bot()
    bot.config = config

    # --- NEW: Register chat manager (Discord adapter only for now) ---
    chat = ChatManager(default="discord")
    chat.register("discord", DiscordChatClient(bot))
    bot.chat = chat  # attach to bot instance so cogs can call self.bot.chat

    # --- Load all cogs ---
    await bot.load_extension("src.cogs.events_cog")
    await bot.load_extension("src.cogs.reminders_cog")

    # --- Optional: start internal HTTP server for cron pings ---
    asyncio.create_task(start_http_server(bot, host="127.0.0.1", port=8088))

    # --- Run the bot ---
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
