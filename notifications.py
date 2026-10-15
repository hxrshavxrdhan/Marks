"""Provider boundary: future Cloud API integration belongs here, not in the UI."""
import re
from urllib.parse import urlencode

def phone_number(raw, country):
    raw = raw.strip()
    if not re.fullmatch(r'\+?[0-9 ()-]+', raw):
        raise ValueError('Parent phone number is missing or invalid')
    digits = re.sub(r'\D', '', raw)
    if not raw.startswith('+') and len(digits) == 10:
        digits = country + digits
    if not re.fullmatch(r'[1-9][0-9]{7,14}', digits):
        raise ValueError('Use a valid international phone number')
    return digits

def prepare(student, assessment, counsellor, country):
    number = phone_number(student['phone'], country)
    lines = ['Dear Parent/Guardian,', '', f"{assessment} marks for {student['name']}:"]
    for subject, value in student['marks'].items():
        lines.append(f"{subject}: {format(value, 'g') if value is not None else 'Not recorded'}")
    lines.extend(['', 'Regards,', counsellor])
    message = '\n'.join(lines)
    return {'studentId': student['id'], 'name': student['name'], 'phone': number, 'message': message,
            'url': 'https://wa.me/' + number + '?' + urlencode({'text': message}), 'warnings': student['warnings']}

class MockProvider:
    def send(self, notification):
        return {**notification, 'status': 'simulated', 'detail': 'Mock only. No message was sent.'}

class CloudAPIProvider:
    def send(self, notification):
        raise NotImplementedError('Configure server-side credentials, approved templates, consent, retries and delivery webhooks before enabling real sends.')
