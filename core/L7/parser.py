from dataclasses import dataclass

@dataclass
class HTTPRequest:
    method: str
    path: str
    headers: dict[str, str]
    body: str

def parse(raw: bytes) -> HTTPRequest:
    text = raw.decode('utf-8')
    header_section, _, body = text.partition('\r\n\r\n')
    lines = header_section.split('\r\n')

    method, path, _ = lines[0].split(' ')

    headers = {}
    for line in lines[1:]:
        key, _, value = line.partition(': ')
        headers[key] = value

    return HTTPRequest(method=method, path=path, headers=headers, body=body)
