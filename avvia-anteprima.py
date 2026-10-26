#!/usr/bin/env python3
"""Apre free-my-tv-matchday.html su http://localhost:8787 e fa da ponte (proxy) verso i siti che non rispondono
a una pagina aperta dal browser: football-data.org, TheSportsDB e le immagini TMDB (per estrarne i colori).

    python3 avvia-anteprima.py        (Windows: py avvia-anteprima.py)

Tienilo nella stessa cartella dell'HTML. Ascolta solo su questo computer (127.0.0.1); le chiavi passano solo
da qui ai rispettivi siti. Ctrl+C per fermarlo. Solo Python 3, nessuna installazione.
"""
import http.server
import os
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

PORT = 8787
PAGE = 'free-my-tv-matchday.html'
ALLOWED = {'api.football-data.org', 'www.thesportsdb.com', 'image.tmdb.org', 'api.jolpi.ca', 'api.themoviedb.org', 'api.open-meteo.com'}
HERE = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=HERE, **k)

    def log_message(self, fmt, *args):
        if '/proxy' in (args[0] if args else ''):
            sys.stderr.write('  ' + (fmt % args) + '\n')

    def do_GET(self):
        if self.path == '/':
            self.send_response(302)
            self.send_header('Location', '/' + PAGE)
            self.end_headers()
            return
        if self.path == '/proxy/ping':
            return self.reply(200, b'fmtv', 'text/plain')
        if self.path.startswith('/proxy?'):
            return self.proxy()
        super().do_GET()

    def reply(self, code, body, ctype):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def proxy(self):
        url = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).get('u', [''])[0]
        host = urllib.parse.urlsplit(url).hostname or ''
        if not url.startswith('https://') or host not in ALLOWED:
            return self.reply(403, b'host non permesso', 'text/plain')
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 FreeMyTV-preview', 'Accept': '*/*'})
        for h in ('X-Auth-Token', 'Authorization'):
            if self.headers.get(h):
                req.add_header(h, self.headers[h])
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                self.reply(r.status, r.read(), r.headers.get('Content-Type', 'application/octet-stream'))
        except urllib.error.HTTPError as e:
            self.reply(e.code, e.read(), 'application/json')
        except Exception as e:
            self.reply(502, str(e).encode('utf-8'), 'text/plain')


def main():
    if not os.path.exists(os.path.join(HERE, PAGE)):
        sys.exit('Metti questo script nella stessa cartella di ' + PAGE)
    server = http.server.ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    url = 'http://localhost:%d/%s' % (PORT, PAGE)
    print('Anteprima su ' + url + '  (Ctrl+C per fermare)')
    threading.Timer(.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nFermato.')


if __name__ == '__main__':
    main()
