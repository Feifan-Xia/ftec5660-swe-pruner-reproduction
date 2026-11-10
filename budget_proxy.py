"""Loopback OpenAI proxy: serial, conservative preflight ceiling and usage ledger."""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import time
import httpx

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=float, default=1.0)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    env = dict(line.split('=', 1) for line in (ROOT / '.env').read_text().splitlines() if '=' in line)
    ledger = ROOT / 'runs/api_usage.jsonl'
    ledger.parent.mkdir(exist_ok=True)
    # Include initial connectivity request conservatively at list cost.
    spent = 0.0000297
    if ledger.exists():
        spent += sum(json.loads(line)['charged_bound_usd'] for line in ledger.read_text().splitlines()
                     if json.loads(line).get('error') != 'ConnectError')
    client = httpx.Client(timeout=180)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            nonlocal spent
            payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            if self.path != '/v1/chat/completions' or payload.get('model') != 'deepseek-v4.1-flash':
                self.send_error(400, 'Unsupported route or model')
                return
            # UTF-8 bytes upper-bound token count conservatively, including tool schemas.
            max_output = min(int(payload.get('max_completion_tokens') or payload.get('max_tokens') or 4096), 4096)
            payload.pop('max_completion_tokens', None)
            payload['max_tokens'] = max_output
            bound = ((len(json.dumps(payload, ensure_ascii=False).encode()) + 4096) * .30 + max_output * 1.20) / 1e6
            if spent + bound > args.limit:
                self.send_error(402, 'Reproduction pilot budget reached')
                return
            streaming = payload.get('stream', False)
            if streaming:
                payload['stream_options'] = {'include_usage': True}
            session = self.headers.get('x-opencode-session', 'ftec5660-pilot')
            headers = {'Authorization': 'Bearer ' + env['OPENAI_API_KEY'],
                       'User-Agent': 'ftec5660-sweqa-reproduction/0.1', 'x-opencode-session': session}
            started = time.time()
            usage = {}
            status = 0
            try:
                # Buffer the response to retain usage even if the downstream client disconnects.
                response = client.post(env['OPENAI_BASE_URL'] + '/chat/completions',
                                      headers=headers, json=payload, timeout=180)
                status = response.status_code
                if streaming:
                    for line in response.text.splitlines():
                        if line.startswith('data: ') and line[6:] != '[DONE]':
                            item = json.loads(line[6:])
                            if item.get('usage'):
                                usage = item['usage']
                else:
                    usage = response.json().get('usage', {})
                actual = (usage.get('prompt_tokens', 0) * .30 + usage.get('completion_tokens', 0) * 1.20) / 1e6
                charge = actual if usage else bound
                spent += charge
                record = dict(time=time.time(), session=session, status=status, seconds=time.time()-started,
                              usage=usage, charged_bound_usd=charge, total_bound_usd=spent)
                with ledger.open('a') as file:
                    file.write(json.dumps(record) + '\n')
                self.send_response(status)
                self.send_header('Content-Type', response.headers.get('content-type', 'application/json'))
                self.send_header('Content-Length', str(len(response.content)))
                self.end_headers()
                self.wfile.write(response.content)
            except Exception as exc:
                if status == 0:
                    charge = 0 if isinstance(exc, httpx.ConnectError) else bound
                    spent += charge
                    with ledger.open('a') as file:
                        file.write(json.dumps(dict(time=time.time(), session=session, status=0,
                            error=type(exc).__name__, charged_bound_usd=charge, total_bound_usd=spent)) + '\n')
                self.close_connection = True

    print(f'Budget proxy on 127.0.0.1:{args.port}; limit={args.limit}; spent_bound={spent}', flush=True)
    HTTPServer(('127.0.0.1', args.port), Handler).serve_forever()


if __name__ == '__main__':
    main()
