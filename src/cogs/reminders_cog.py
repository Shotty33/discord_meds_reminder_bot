from __future__ import annotations
import asyncio
import logging
from datetime import datetime
from typing import List, Tuple, Optional

import pytz
from discord.ext import commands, tasks

logger = logging.getLogger(__name__)


class RemindersCog(commands.Cog):
    """
    Medication reminder commands + minute-precision dispatcher.

    - Background task runs every minute (discord.ext.tasks)
    - Uses RemindersManager + RemindersDAO under the hood
    - Sends DMs via platform-agnostic ChatManager (attached on bot as `bot.chat`)
    - Guarded init so commands still register even if init fails
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.manager = None
        self.controller = None
        self._init_error: Optional[str] = None

        logger.info("RemindersCog: initializing...")
        try:
            # Lazy imports so command registration isn't blocked if init fails
            from src.services.database_manager import DatabaseManager
            from src.dao.reminders_dao import RemindersDAO
            from src.services.reminders_manager import RemindersManager
            from src.controllers.reminders_controller import RemindersController

            # Build DB/DAO/Manager with config from bot
            db = DatabaseManager(self.bot.config)
            dao = RemindersDAO(db)
            self.manager = RemindersManager(
                dao,
                default_tz=self.bot.config.get_default_timezone(),
                chat_id=1,                  # 'discord' seeded as id=1 in chats table
                config=self.bot.config,     # pass through AI/paths config
            )

            # Controller (prefer signature with bot; fall back if not present)
            try:
                self.controller = RemindersController(self.manager, self.bot)
            except TypeError:
                self.controller = RemindersController(self.manager)
                setattr(self.controller, "bot", self.bot)

            logger.info("RemindersCog: init complete")

        except Exception as e:
            self._init_error = f"{type(e).__name__}: {e}"
            logger.exception("RemindersCog: init failed: %s", self._init_error)

    # ---------- lifecycle: start/stop the every-minute dispatcher ----------
    async def cog_load(self):
        if not self.auto_dispatch.is_running():
            self.auto_dispatch.start()
            logger.info("RemindersCog: auto_dispatch started (every 1 minute)")

    async def cog_unload(self):
        if self.auto_dispatch.is_running():
            self.auto_dispatch.cancel()
            logger.info("RemindersCog: auto_dispatch stopped")

    # ---------- internal helpers ----------
    def _check_ready(self) -> Optional[str]:
        if self._init_error:
            return f"Init error: {self._init_error}"
        if not self.manager or not self.controller:
            return "Reminders system not ready."
        if not hasattr(self.bot, "chat"):
            return "Chat manager not available on bot."
        return None

    async def _send_after_delay(self, user_id: str, text: str, delay: float):
        try:
            if delay > 0:
                await asyncio.sleep(delay)
            await self.bot.chat.send_dm(user_id, text)
            logger.info("Sent reminder to %s", user_id)
        except Exception as e:
            logger.exception("Send failed to %s: %s", user_id, e)

    # ---------- every-minute loop (minute precision, no dupes) ----------
    @tasks.loop(minutes=1)
    async def auto_dispatch(self):
        try:
            err = self._check_ready()
            if err:
                logger.warning("auto_dispatch blocked: %s", err)
                return

            tz = pytz.timezone(self.bot.config.get_default_timezone())
            now = datetime.now(tz).replace(second=0, microsecond=0)
            hhmm = now.strftime("%H:%M")
            logger.info("Dispatch check at %s", hhmm)

            # Manager returns: List[(user_id, persona, label, send_at_dt)]
            due: List[Tuple[str, str, str, datetime]] = await self.manager.get_due_at_minute(hhmm)
            if not due:
                logger.info("No reminders due at %s", hhmm)
                return

            for user_id, persona, label, send_at in due:
                # Optional username enrichment
                user_name: Optional[str] = None
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    if user and user.name:
                        user_name = user.name
                except Exception:
                    pass

                text = await self.manager.render_message(persona, label, user_name=user_name)
                delay = max(0.0, (send_at - now).total_seconds())  # usually 0s
                self.bot.loop.create_task(self._send_after_delay(user_id, text, delay))

        except Exception as e:
            logger.exception("auto_dispatch failed: %s", e)

    # ---------- commands ----------
    @commands.command(name="r")
    async def create_reminder_cmd(self, ctx: commands.Context):
        err = self._check_ready()
        if err:
            await ctx.send(f"❌ {err}")
            return
        await self.controller.handle_create_reminder(ctx)

    @commands.command(name="l")
    async def list_reminders_cmd(self, ctx: commands.Context):
        err = self._check_ready()
        if err:
            await ctx.send(f"❌ {err}")
            return
        await self.controller.handle_list_reminders(ctx)

    @commands.command(name="dr")
    async def delete_reminder_cmd(self, ctx: commands.Context, time: str, *, label: str):
        err = self._check_ready()
        if err:
            await ctx.send(f"❌ {err}")
            return
        await self.controller.handle_delete_reminder(ctx, time, label)

    @commands.command(name="helpme")
    async def helpme(self, ctx: commands.Context):
        await ctx.send(
            "Commands:\n"
            "`!r`                - interactively add a new reminder\n"
            "`!l`                - list your reminders\n"
            "`!dr HH:MM <label>` - delete a reminder\n"
            "`!helpme`           - show this help message\n"
        )

    @commands.command(name="runbatch")
    async def runbatch_cmd(self, ctx: commands.Context):
        """Manual trigger for testing: run minute-precision dispatch now."""
        await ctx.send("Running minute-precision dispatch for the current time…")
        await self.auto_dispatch()  # run once immediately
        await ctx.send("Dispatch attempt complete.")

    @commands.command(name="aistatus")
    async def aistatus(self, ctx: commands.Context):
        err = self._check_ready()
        if err:
            await ctx.send(f"❌ {err}")
            return
        ai = self.manager.ai
        await ctx.send(
            f"AI provider={ai.provider}, model={ai.model}, enabled={ai.enabled}, host={ai.ollama_host}"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(RemindersCog(bot))
