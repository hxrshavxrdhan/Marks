import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from workbook import read_students
from notifications import prepare, phone_number, MockProvider, CloudAPIProvider

class AppTests(unittest.TestCase):
    def setUp(self):
        self.students = read_students(Path(__file__).resolve().parents[1] / 'data/Book7.xlsx')

    def test_source_fidelity(self):
        self.assertEqual([s['name'] for s in self.students], ['harsha', 'raghu', 'coordinator'])
        self.assertEqual([list(s['marks'].values()) for s in self.students], [[97,76,30,48],[56,78,89,89],[100,100,100,101]])
        self.assertEqual(len(self.students[2]['warnings']), 2)

    def test_message_and_encoding(self):
        item = prepare(self.students[0], 'Internal & Review', 'Dr. Example', '91')
        self.assertIn('MATHS: 97', item['message'])
        self.assertIn('Internal+%26+Review', item['url'])
        self.assertTrue(item['phone'].startswith('91'))
        self.assertEqual(MockProvider().send(item)['status'], 'simulated')

    def test_phone_validation(self):
        self.assertEqual(phone_number('+44 7700 900123', '91'), '447700900123')
        for bad in ['', 'abc', '123', '+0000000000']:
            with self.assertRaises(ValueError): phone_number(bad, '91')

    def test_cloud_is_disabled(self):
        with self.assertRaises(NotImplementedError): CloudAPIProvider().send({})

    def test_missing_marks_preserved(self):
        student={**self.students[0], 'marks':{'MATHS':0, 'UHV':None}}
        message=prepare(student,'Test','Counsellor','91')['message']
        self.assertIn('MATHS: 0',message)
        self.assertIn('UHV: Not recorded',message)

if __name__ == '__main__': unittest.main()
