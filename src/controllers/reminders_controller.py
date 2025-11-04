import asyncio
import discord
import logging
from discord.ext import commands

logger = logging.getLogger(__name__)

class RemindersController:
    def __init__(self, manager, bot=None):
        self.reminders_manager = manager
        self.bot = bot  # set by cog if not passed

    async def _prompt_user(self, ctx: commands.Context, prompt_text: str, timeout_seconds: int = 30):
        await ctx.send(prompt_text)

        def check(message: discord.Message):
            return message.author == ctx.author and message.channel == ctx.channel

        try:
            response_msg = await self.bot.wait_for("message", check=check, timeout=timeout_seconds)
            return response_msg.content.strip()
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Please start over with `!r`.")
            logger.warning("User %s timed out: %s", ctx.author.id, prompt_text)
            return None

    async def handle_create_reminder(self, ctx: commands.Context) -> None:
        try:
            persona = await self._prompt_user(ctx, "Who should remind you? (ex: batman, gremlin best friend, soft voice)")
            if persona is None:
                return

            time_str = await self._prompt_user(ctx, "What time should I remind you? (24-hour HH:MM, ex: 08:00, 14:30)")
            if time_str is None:
                return

            label = await self._prompt_user(ctx, "What do you want to be reminded to do? (ex: Take Adderall, Drink water, Do stretches)")
            if label is None:
                return

            user_id = str(ctx.author.id)

            # ✅ IMPORTANT: await the manager call
            success, message = await self.reminders_manager.create_reminder(
                user_id=user_id,
                persona=persona,
                time_str=time_str,
                label=label,
            )

            await ctx.send(message)
            logger.info("User %s create_reminder result (success=%s): %s", user_id, success, message)

        except Exception as e:
            logger.exception("handle_create_reminder failed: %s", e)
            await ctx.send("❌ Something went wrong creating the reminder. Check logs.")
            return

    async def handle_list_reminders(self, ctx: commands.Context) -> None:
        try:
            user_id = str(ctx.author.id)
            success, message = await self.reminders_manager.get_reminders(user_id)  # ✅ await
            await ctx.send(message)
        except Exception as e:
            logger.exception("handle_list_reminders failed: %s", e)
            await ctx.send("❌ Couldn’t list reminders. Check logs.")

    async def handle_delete_reminder(self, ctx: commands.Context, time: str, label: str) -> None:
        try:
            user_id = str(ctx.author.id)
            success, message = await self.reminders_manager.delete_reminder(user_id, time, label)  # ✅ await
            await ctx.send(message)
        except Exception as e:
            logger.exception("handle_delete_reminder failed: %s", e)
            await ctx.send("❌ Couldn’t delete that reminder. Check logs.")
