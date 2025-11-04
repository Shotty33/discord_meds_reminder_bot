import logging
import discord
from src.utils.types import ChatClient

logger = logging.getLogger(__name__)

class DiscordChatClient(ChatClient):
    """
    Discord adapter that implements the generic ChatClient interface.
    Responsible for sending DMs or messages via the discord.py API.
    """

    def __init__(self, bot: discord.Client):
        self.bot = bot

    async def send_dm(self, user_id: str, text: str) -> None:
        """
        Send a direct message to a Discord user.
        :param user_id: The user's Discord ID (string or int)
        :param text: The message to send
        """
        try:
            user = await self.bot.fetch_user(int(user_id))
            if user is None:
                logger.warning("DiscordChatClient: Could not fetch user %s", user_id)
                return

            await user.send(text)
            logger.info("Sent DM to user %s", user_id)

        except discord.Forbidden:
            logger.warning("DiscordChatClient: Cannot DM user %s (DMs disabled)", user_id)

        except discord.HTTPException as e:
            logger.error("DiscordChatClient: Failed to send DM to %s: %s", user_id, e)

        except Exception as e:
            logger.exception("DiscordChatClient: Unexpected error sending to %s: %s", user_id, e)
