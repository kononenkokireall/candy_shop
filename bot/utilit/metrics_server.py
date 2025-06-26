# bot/utilit/metrics_server.py
from aiohttp import web
from prometheus_client import  generate_latest

async def metrics_handler(request):
    data = generate_latest()
    return web.Response(body=data, content_type="text/plain; version=0.0.4")

async def run_metrics_server(host: str = "0.0.0.0", port: int = 8000):
    app = web.Application()
    app.router.add_get("/metrics", metrics_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port)
    await site.start()
