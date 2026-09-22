import asyncio
from core.L4.algorithms import RoundRobin, LeastConnections, IPHash
from core.L4.syn_flood import SYNFloodDetector

class L4Proxy:
    def __init__(self, backends: list[tuple[str, int]], algorithm: str = "round_robin", syn_flood_threshold: int = 10, syn_flood_block_duration: int = 60):
        algorithms = {
            "round_robin": RoundRobin(backends),
            "least_connections": LeastConnections(backends),
            "ip_hash": IPHash(backends)
        }
        self.algorithm = algorithms[algorithm]
        self.detector = SYNFloodDetector(threshold=syn_flood_threshold, block_duration=syn_flood_block_duration)

    async def handle_client(self, reader, writer):
        client_ip = writer.get_extra_info('peername')[0]
        
        if self.detector.is_blocked(client_ip):
            print(f"Blocked IP: {client_ip}")
            writer.close()
            return

        self.detector.connection_received(client_ip)
        print(f"Half-open count for {client_ip}: {self.detector.half_open[client_ip]}")

        backend_host, backend_port = self.algorithm.next_backend(client_ip)
        self.algorithm.increment((backend_host, backend_port))

        try:
            backend_reader, backend_writer = await asyncio.open_connection(backend_host, backend_port)
        
            async def forward(src, dst):
                first_read = True
                while True:
                    data = await src.read(1024)
                    if not data:
                        break
                    if first_read and src is reader:
                        self.detector.connection_completed(client_ip)
                        first_read = False
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
