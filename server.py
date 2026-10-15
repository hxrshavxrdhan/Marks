"""Local prototype: Python 3.10+, no dependencies, bound to loopback only."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from notifications import MockProvider, prepare
from workbook import read_students

ROOT = Path(__file__).resolve().parent
PORT = int(os.environ.get('PORT', '8000'))

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Avoid logging parent phone numbers or notification contents.

    def reply(self, code, payload, kind='application/json'):
        body = json.dumps(payload).encode() if kind == 'application/json' else payload
        self.send_response(code)
        self.send_header('Content-Type', kind + '; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/api/students':
            try:
                self.reply(200, {'students': read_students(ROOT / 'data/Book7.xlsx'), 'source': 'Book7.xlsx · Sheet1', 'mode': 'mock'})
            except (ValueError, OSError, KeyError) as error:
                self.reply(500, {'error': str(error)})
            return
        files = {'/': ('index.html', 'text/html'), '/app.js': ('app.js', 'text/javascript'), '/styles.css': ('styles.css', 'text/css')}
        if self.path not in files:
            return self.reply(404, {'error': 'Not found'})
        filename, kind = files[self.path]
        self.reply(200, (ROOT / 'public' / filename).read_bytes(), kind)

    def do_POST(self):
        if self.path not in ['/api/preview', '/api/send']:
            return self.reply(404, {'error': 'Not found'})
        origin = self.headers.get('Origin')
        if origin and origin not in [f'http://localhost:{PORT}', f'http://127.0.0.1:{PORT}']:
            return self.reply(403, {'error': 'Origin not allowed'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length < 1 or length > 16384:
                raise ValueError('Invalid request size')
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError('Expected an object')
            ids = data.get('studentIds')
            if not isinstance(ids, list) or not ids or not all(isinstance(i, str) for i in ids):
                raise ValueError('Select one or more students')
            options = {}
            for key, default in [('assessment', 'Internal Assessment 1'), ('counsellor', 'Class Counsellor'), ('country', '91')]:
                value = data.get(key, default)
                if not isinstance(value, str) or not value.strip() or len(value) > 100:
                    raise ValueError('Invalid ' + key)
                options[key] = value.strip()
            if not options['country'].isdigit() or not 1 <= len(options['country']) <= 3 or options['country'][0] == '0':
                raise ValueError('Country code must contain 1–3 digits, without +')
            students = {s['id']: s for s in read_students(ROOT / 'data/Book7.xlsx')}
            if any(i not in students for i in ids):
                raise ValueError('Unknown student')
            results = []
            for student_id in dict.fromkeys(ids):
                student = students[student_id]
                try:
                    item = prepare(student, **options)
                    results.append(MockProvider().send(item) if self.path == '/api/send' else {**item, 'status': 'ready'})
                except ValueError as error:
                    results.append({'studentId': student_id, 'name': student['name'], 'status': 'failed', 'detail': str(error)})
            self.reply(200, {'results': results, 'mode': 'mock'})
        except (ValueError, TypeError) as error:
            self.reply(400, {'error': str(error)})

if __name__ == '__main__':
    print(f'Counsellor Marks running at http://127.0.0.1:{PORT}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
