import time
import asyncio
from core.L7.parser import HTTPRequest, parse
from core.L7.bot_detection import is_bot_by_headers, is_bot_by_cadence, is_bot_by_connection_timing
from core.L7.algorithms import route_request
from core.L4.algorithms import RoundRobin, LeastConnections, IPHash

class L7Proxy:
    def __init__(self, routes: list[dict], algorithm: str = "round_robin"):
        self.routes = routes
        self.pools = {}
        for route in routes:
            backends = [(b["host"], b["port"]) for b in route["backends"]]
            algorithms = {
                "round_robin": RoundRobin(backends),
                "least_connections": LeastConnections(backends),
                "ip_hash": IPHash(backends)
            }
            self.pools[route["path"]] = algorithms[algorithm]
       
    async def handle_client(self, reader, writer):
        connection_time = time.time()
        client_ip = writer.get_extra_info('peername')[0]
        
        try:
            raw = await reader.read(4096)
            if not raw:
                return
            
            request_time = time.time()
            request = parse(raw)
            
            if is_bot_by_headers(request) or is_bot_by_cadence(client_ip) or is_bot_by_connection_timing(connection_time, request_time):
                writer.write(b"HTTP/1.1 403 Forbidden\r\n\r\n")
                await writer.drain()
                return
            
            backends = route_request(request, self.routes)
            if not backends:
                writer.write(b"HTTP/1.1 404 Not Found\r\n\r\n")
                await writer.drain()
                return
            
            backend_host, backend_port = self.pools[request.path].next_backend(client_ip)
            b_reader, b_writer = await asyncio.open_connection(backend_host, backend_port)
            b_writer.write(raw)
            await b_writer.drain()
            
            response = await b_reader.read(4096)
            writer.write(response)
            await writer.drain()
            
        finally:
            writer.close()

    async def start(self, host: str, port: int):
        server = await asyncio.start_server(self.handle_client, host, port, reuse_port=True)
        async with server:
            await server.serve_forever()
