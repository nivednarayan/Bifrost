import asyncio
from core.L4.proxy import L4Proxy

async def main():
    backends = [
        ('localhost', 9001),
        ('localhost', 9002),
    ]
    proxy = L4Proxy(backends, algorithm="ip_hash")
    await proxy.start('0.0.0.0', 9000)

asyncio.run(main())
