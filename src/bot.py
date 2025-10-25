# bot.py
import logging
import asyncio
import discord
from discord.ext import commands

from .utils.config_loader import ConfigLoader
from .services.database_manager import DatabaseManager
from .services.reminders_manager import RemindersManager


# -------------------------------------------------
# Logging setup
# -------------------------------------------------
# Configure root logger for console output only
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler()],
)

# Create a named logger so other modules can import it
logger = logging.getLogger()

# -------------------------------------------------
# Build shared services / singletons
# -------------------------------------------------
config = ConfigLoader()
db_manager = DatabaseManager(config)
reminders = RemindersManager(config, db_manager)

DISCORD_TOKEN = config.get_discord_token()

# -------------------------------------------------
# Discord bot setup
# -------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True  # needed to read prompt replies

bot = commands.Bot(command_prefix="!", intents=intents)


async def prompt_user(ctx, prompt_text: str, timeout_seconds: int = 30) -> str | None:
    """
    Ask the user something and wait for their response in the same channel/DM.
    Timeout -> returns None.
    """
    await ctx.send(prompt_text)

    def check(message: discord.Message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        response_msg = await bot.wait_for("message", check=check, timeout=timeout_seconds)
        return response_msg.content.strip()
    except asyncio.TimeoutError:
        await ctx.send("You took too long to respond. Please start over.")
        return None


@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user.name}")


# -----------------------------
# Commands
# -----------------------------

@bot.command(name="r")
async def create_reminder_cmd(ctx: commands.Context):
    """
    Interactive reminder creation.
    Flow:
      1. persona
      2. time
      3. label
    Calls ReminderService.create_reminder(...)
    """

    persona = await prompt_user(
        ctx,
        "Who should remind you? (ex: `batman`, `gremlin best friend`, `soft voice`)"
    )
    if persona is None:
        return

    time_str = await prompt_user(
        ctx,
        "What time should I remind you? (24-hour HH:MM, ex: `08:00`, `14:30`)"
    )
    if time_str is None:
        return

    label = await prompt_user(
        ctx,
        "What do you want to be reminded to do? (ex: `Take Adderall`, `Drink water`, `Do stretches`)"
    )
    if label is None:
        return

    user_id = str(ctx.author.id)
    success, message = reminders.create_reminder(
        user_id=user_id,
        persona=persona,
        time_str=time_str,
        label=label,
    )

    await ctx.send(message)


@bot.command(name="l")
async def list_reminders_cmd(ctx: commands.Context):
    """
    List all active reminders for this user.
    Uses ReminderService.get_reminders(...)
    """
    user_id = str(ctx.author.id)
    success, message = reminders.get_reminders(user_id)
    await ctx.send(message)


@bot.command(name="dr")
async def delete_reminder_cmd(ctx: commands.Context, time: str, *, label: str):
    """
    Delete a reminder by matching time + label.
    Uses ReminderService.delete_reminder(...)
    Usage:
      !dr 08:00 Take Adderall
    """
    user_id = str(ctx.author.id)
    success, message = reminders.delete_reminder(user_id, time, label)
    await ctx.send(message)


@bot.command(name="helpme")
async def help_command(ctx: commands.Context):
    await ctx.send(
        "Commands:\n"
        "`!r`                - interactively add a new reminder\n"
        "`!l`                - list your reminders\n"
        "`!dr HH:MM <label>` - delete a reminder\n"
        "`!helpme`           - show this help message\n"
    )


# -------------------------------------------------
# Run the bot
# -------------------------------------------------
bot.run(DISCORD_TOKEN)
