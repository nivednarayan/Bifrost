import asyncio
from core.L4.proxy import L4Proxy
from core.L7.proxy import L7Proxy
from config import Config

async def _run(config : Config):
    proxyL4 = L4Proxy(config.backends, config.algorithm, config.syn_flood_threshold, config.syn_flood_block_duration)
    proxyL7 = L7Proxy(config, config.route, config.algorithm)
    await asyncio.gather(proxyL4.start('0.0.0.0', config.listen_port), proxyL7.start('0.0.0.0', config.l7_port))

def worker_proxy(config: Config):
    asyncio.run(_run(config))
