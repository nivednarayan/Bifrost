import time
import asyncio
from core.L7.parser import HTTPRequest, parse
from core.L7.bot_detection import is_bot_by_headers, is_bot_by_cadence, is_bot_by_connection_timing
from core.L7.algorithms import route_request
from core.L4.algorithms import RoundRobin, LeastConnections, IPHash
from pool.connection_pool import ConnectionPool
from pool.health import HealthChecker, CircuitBreaker

class L7Proxy:
    def __init__(self, config, routes: list[dict], algorithm: str = "round_robin"):
        self.config = config
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

        self.connection_pools = {}
        self.circuit_breakers = {}
        for route in routes:
            for b in route["backends"]:
                key = (b["host"], b["port"])
                self.connection_pools[key] = ConnectionPool(b["host"], b["port"], max_pool_size=config.max_pool_size, ttl=60)
                self.circuit_breakers[key] = CircuitBreaker()

        self.health_checker = HealthChecker(list(self.circuit_breakers.keys()))

    async def handle_client(self, reader, writer):
        connection_time = time.time()
        client_ip = writer.get_extra_info('peername')[0]
        b_reader, b_writer, backend_host, backend_port, route, response_complete = None, None, None, None, None, False

        try:
            raw = await reader.read(4096)
            if not raw:
                return

            request_time = time.time()
            request = parse(raw)

            if self.config.bot_detection and (is_bot_by_headers(request) or is_bot_by_cadence(client_ip)): # or is_bot_by_connection_timing(connection_time, request_time):
                writer.write(b"HTTP/1.1 403 Forbidden\r\n\r\n")
                await writer.drain()
                return

            route = route_request(request, self.routes)
            if not route:
                writer.write(b"HTTP/1.1 404 Not Found\r\n\r\n")
                await writer.drain()
                return

            backend_host, backend_port = self.pools[route["path"]].next_backend(client_ip)
            self.pools[route["path"]].increment((backend_host, backend_port))

            if self.circuit_breakers[(backend_host, backend_port)].is_open():
                writer.write(b"HTTP/1.1 503 Service Unavailable\r\n\r\n")
                await writer.drain()
                return

            try:
                b_reader, b_writer = await self.connection_pools[(backend_host, backend_port)].acquire()
                b_writer.write(raw)
                await b_writer.drain()
                
                # read headers
                header_data = b""
                while b"\r\n\r\n" not in header_data:
                    chunk = await b_reader.read(4096)
                    if not chunk:
                        raise Exception("Backend closed connection")
                    header_data += chunk

                # split headers and any body bytes that came with them
                header_part, body_part = header_data.split(b"\r\n\r\n", 1)

                # parse content-length
                content_length = 0
                for line in header_part.split(b"\r\n")[1:]:
                    if line.lower().startswith(b"content-length:"):
                        content_length = int(line.split(b":")[1].strip())
                        break

                # read remaining body
                while len(body_part) < content_length:
                    chunk = await b_reader.read(4096)
                    if not chunk:
                        break
                    body_part += chunk

                response = header_part + b"\r\n\r\n" + body_part
                response_complete = True
                self.circuit_breakers[(backend_host, backend_port)].record_success()
                writer.write(response)
                await writer.drain()

            except Exception:
                self.circuit_breakers[(backend_host, backend_port)].record_failure()
                writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                await writer.drain()

        finally:
            if backend_host and backend_port and route:
                self.pools[route["path"]].decrement((backend_host, backend_port))
            if b_writer is not None:
                if response_complete:
                    self.connection_pools[(backend_host, backend_port)].release(b_reader, b_writer, time.time())
                else:
                    b_writer.close()

    async def start(self, host: str, port: int):
        server = await asyncio.start_server(self.handle_client, host, port, reuse_port=True)
        async with server:
            await server.serve_forever()
