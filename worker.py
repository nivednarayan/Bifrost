import asyncio
from core.L4.proxy import L4Proxy
from config import Config

def worker_proxy(config : Config):
    proxy = L4Proxy(config.backends, config.algorithm, config.syn_flood_threshold, config.syn_flood_block_duration)
    asyncio.run(proxy.start('0.0.0.0', config.listen_port))

