import asyncio
from core.L4.algorithms import RoundRobin, LeastConnections, IPHash

class L4Proxy:
    def __init__(self, backends: list[tuple[str, int]], algorithm: str = "round_robin"):
        algorithms = {
            "round_robin": RoundRobin(backends),
            "least_connections": LeastConnections(backends),
            "ip_hash": IPHash(backends)
        }
        self.algorithm = algorithms[algorithm]

    async def handle_client(self, reader, writer):
        client_ip = writer.get_extra_info('peername')[0]
        backend_host, backend_port = self.algorithm.next_backend(client_ip)

        self.algorithm.increment((backend_host, backend_port))

        try:
            backend_reader, backend_writer = await asyncio.open_connection(backend_host, backend_port)

            async def forward(src, dst):
                while True:
                    data = await src.read(1024)
                    if not data:
                        break
                    dst.write(data)
                    await dst.drain()
                dst.close()

            await asyncio.gather(
                forward(reader, backend_writer),
                forward(backend_reader, writer)
            )
        finally:
            self.algorithm.decrement((backend_host, backend_port))
            writer.close()

    async def start(self, host: str, port: int):
        server = await asyncio.start_server(self.handle_client, host, port)
        async with server:
            await server.serve_forever()
