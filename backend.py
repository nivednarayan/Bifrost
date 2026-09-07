import asyncio
import sys

port = int(sys.argv[1])

async def handle_client(reader, writer):
    while True:
        data = await reader.read(1024)
        if not data:
            break
        response = f"Backend:{port} : {data.decode()}".encode()
        writer.write(response)
        await writer.drain()
    writer.close()

async def main():
    server = await asyncio.start_server(handle_client, '0.0.0.0', port)
    async with server:
        await server.serve_forever()

asyncio.run(main())
