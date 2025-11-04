import logging
from discord.ext import commands

logger = logging.getLogger(__name__)

class EventsCog(commands.Cog):
    """General bot events & one-time slash command sync."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._synced = False

    @commands.Cog.listener()
    async def on_ready(self):
        if not self._synced:
            try:
                await self.bot.tree.sync()
                self._synced = True
                user = getattr(self.bot, "user", None)
                logger.info("App commands synced. Bot is ready%s", f" as {user.name}" if user else "")
            except Exception as e:
                logger.exception("Failed to sync app commands: %s", e)
        else:
            logger.info("Bot ready (already synced).")

async def setup(bot: commands.Bot):
    await bot.add_cog(EventsCog(bot))
