"""Read-only official MCP transport. No credentials or responses are persisted."""
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error

URL = 'https://mcp.mcd.cn'
ALLOWED = {'delivery-query-addresses', 'delivery-query-stores', 'query-meals',
           'query-meal-detail', 'query-store-coupons', 'calculate-price'}

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Official endpoint redirect refused')

def credentials():
    token = os.environ.get('MCD_MCP_TOKEN')
    if token:
        return 'Bearer ' + token
    try:
        result = subprocess.run(['codex', 'mcp', 'get', 'mcd-mcp', '--json'],
                                capture_output=True, text=True, encoding='utf-8',
                                check=True, timeout=15)
        transport = json.loads(result.stdout)['transport']
        if transport.get('url', '').rstrip('/') != URL:
            raise ValueError('Configured endpoint differs from official endpoint')
        headers = transport.get('http_headers') or {}
        auth = next((v for k, v in headers.items() if k.lower() == 'authorization'), None)
        env_name = transport.get('bearer_token_env_var')
        if not auth and env_name and os.environ.get(env_name):
            auth = 'Bearer ' + os.environ[env_name]
        if not auth:
            raise ValueError('Missing credential')
        return auth
    except Exception:
        raise ValueError('Configure MCD_MCP_TOKEN locally or the Codex mcd-mcp connection') from None

class Client:
    def __init__(self):
        self.headers = {'Authorization': credentials(), 'Content-Type': 'application/json',
                        'Accept': 'application/json, text/event-stream'}
        self.opener = urllib.request.build_opener(NoRedirect())
        self.sequence = 0
        self.call('initialize', {'protocolVersion': '2024-11-05', 'capabilities': {},
                  'clientInfo': {'name': 'maimai-no-drink-readonly', 'version': '0.3'}})
        self.call('notifications/initialized', notification=True)

    def call(self, method, params=None, notification=False):
        self.sequence += 1
        payload = {'jsonrpc': '2.0', 'method': method}
        if not notification:
            payload['id'] = self.sequence
        if params is not None:
            payload['params'] = params
        with self.opener.open(urllib.request.Request(URL, data=json.dumps(payload).encode(),
                                                   headers=self.headers), timeout=30) as response:
            session = response.headers.get('Mcp-Session-Id')
            if session:
                self.headers['Mcp-Session-Id'] = session
            raw = response.read().decode('utf-8')
        if not raw:
            return {}
        if raw.lstrip().startswith('{'):
            result = json.loads(raw)
        else:
            events = [json.loads(line[5:]) for line in raw.splitlines() if line.startswith('data:')]
            result = next((event for event in events if event.get('id') == payload.get('id')), {})
        if 'error' in result:
            raise ValueError('MCP returned a protocol error')
        return result

    def discover(self):
        return [t for t in self.call('tools/list', {})['result']['tools'] if t['name'] in ALLOWED]

    def tool(self, name, arguments):
        if name not in ALLOWED:
            raise ValueError('Tool is outside read-only allowlist')
        result = self.call('tools/call', {'name': name, 'arguments': arguments})['result']
        if result.get('isError'):
            raise ValueError('Official tool failed; do not rank this result')
        return result

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        client = Client()
        name = sys.argv[1] if len(sys.argv) > 1 else 'list'
        result = client.discover() if name == 'list' else client.tool(name, json.load(sys.stdin))
        print(json.dumps(result, ensure_ascii=False))
    except urllib.error.HTTPError as error:
        print('Official service HTTP error: ' + str(error.code), file=sys.stderr)
        sys.exit(1)
    except Exception as error:
        print('Read-only query failed (' + type(error).__name__ + '). Check local connection; no order was made.', file=sys.stderr)
        sys.exit(1)
