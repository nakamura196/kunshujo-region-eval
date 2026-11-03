"""外の帖の枠描き画面（ext_draw.html）を出し、描いた枠をそのたびにファイルへ書く保存係。

    python3 -I tools/kunshujo/ext_draw_server.py <作業フォルダ（frames.json があるところ）> [--port 8767]

  - 127.0.0.1 だけで待ち受ける。http://127.0.0.1:8767/ を開く。画像は IIIF から直接読む（幅 2048）。
  - 保存先は <作業フォルダ>/human/state.json（枠は canvas 原寸の 4 点 [[x,y]×4]。古い版の [x, y, w, h] も混ざりうる。採点時に外接する四角へ直す）。書くたびに前の版を state.prev.json に残す。
  - 画面は機械の枠を一切読まない（白紙から描くため）。
"""
import argparse, json, os, shutil
from http.server import BaseHTTPRequestHandler, HTTPServer

ap = argparse.ArgumentParser()
ap.add_argument('work')
ap.add_argument('--port', type=int, default=8767)
a = ap.parse_args()
HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ext_draw.html')
FRAMES = os.path.join(a.work, 'frames.json')
os.makedirs(os.path.join(a.work, 'human'), exist_ok=True)
STATE = os.path.join(a.work, 'human', 'state.json')


class H(BaseHTTPRequestHandler):
    def send(self, code, body, ctype):
        b = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self.send(200, open(HTML, 'rb').read(), 'text/html; charset=utf-8')
        elif self.path == '/frames.json':
            self.send(200, open(FRAMES, 'rb').read(), 'application/json')
        elif self.path == '/state':
            s = open(STATE, 'rb').read() if os.path.exists(STATE) else b'{}'
            self.send(200, s, 'application/json')
        else:
            self.send(404, 'not found', 'text/plain')

    def do_POST(self):
        if self.path != '/state':
            return self.send(404, 'not found', 'text/plain')
        d = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        if os.path.exists(STATE):
            shutil.copyfile(STATE, STATE.replace('.json', '.prev.json'))
        tmp = STATE + '.tmp'
        json.dump(d, open(tmp, 'w'), ensure_ascii=False)
        os.replace(tmp, STATE)
        self.send(200, 'ok', 'text/plain')

    def log_message(self, *args):
        pass


print(f'http://127.0.0.1:{a.port}/  →  {STATE}')
HTTPServer(('127.0.0.1', a.port), H).serve_forever()
