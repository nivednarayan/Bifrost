import asyncio
import sys

backend = str(sys.argv[1])
port = int(sys.argv[2])

async def handle_client(reader, writer):
    data = await reader.read(1024)
    if data:
        body = f"{backend}:{port} : {data.decode()}"
        response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nConnection: close\r\nContent-Length: {len(body)}\r\n\r\n{body}"
        writer.write(response.encode())
        await writer.drain()
    writer.close()

async def main():
    server = await asyncio.start_server(handle_client, '0.0.0.0', port)
    async with server:
        await server.serve_forever()

asyncio.run(main())
