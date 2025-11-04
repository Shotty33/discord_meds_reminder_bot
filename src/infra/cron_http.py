import logging

from aiohttp import web

logger = logging.getLogger(__name__)

async def make_app(bot) -> web.Application:
    app = web.Application()

    async def health(_request):
        return web.json_response({"ok": True})

    async def dispatch(_request):
        cog = bot.get_cog("RemindersCog")
        if not cog:
            return web.json_response({"ok": False, "error": "RemindersCog not loaded"}, status=500)
        await cog.run_batch(window_minutes=15)
        return web.json_response({"ok": True})

    app.router.add_get("/health", health)
    app.router.add_post("/cron/dispatch", dispatch)
    return app

async def start_http_server(bot, host="127.0.0.1", port=8088):
    app = await make_app(bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info("Cron HTTP server listening on http://%s:%s", host, port)
