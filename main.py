import asyncio
from core.L4.proxy import L4Proxy
from config import load_config

async def main():
    config = load_config("config.yaml")
    proxy = L4Proxy(config.backends, config.algorithm, config.syn_flood_threshold, config.syn_flood_block_duration)
    await proxy.start('0.0.0.0', config.listen_port)

asyncio.run(main())
