"""blind50/index.html の判定を、そのたびにファイルへ書き出す保存係

    python3 -I tools/kunshujo/blind50_server.py strengthening/kunshujo-eval/classify/b1-test300/blind50

127.0.0.1:8766 だけで待ち受ける。ページ（file:// のままでよい）が判定のたびに全件を送ってくるので、
<dir>/results.json と <dir>/author50_blind.tsv を置き換える。ページを作り直しても、この 2 つは消えない。
"""
import json, os, sys
from http.server import BaseHTTPRequestHandler, HTTPServer

D = sys.argv[1]
J, T = os.path.join(D, 'results.json'), os.path.join(D, 'author50_blind.tsv')


def write(path, text):
    tmp = path + '.tmp'
    with open(tmp, 'w') as f:
        f.write(text)
    os.replace(tmp, path)


class H(BaseHTTPRequestHandler):
    def _head(self, code=200):
        self.send_response(code)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()

    def do_OPTIONS(self):
        self._head()

    def do_GET(self):
        self._head()
        self.wfile.write(open(J, 'rb').read() if os.path.exists(J) else b'{"state": {}}')

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        write(J, json.dumps({'state': body['state']}, ensure_ascii=False, indent=1))
        write(T, body['tsv'] + '\n')
        self._head()
        self.wfile.write(b'{"ok": true}')

    def log_message(self, *a):
        pass


HTTPServer(('127.0.0.1', 8766), H).serve_forever()
