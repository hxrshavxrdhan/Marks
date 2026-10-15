"""Read the supplied Excel layout without third-party dependencies."""
import re
import zipfile
import xml.etree.ElementTree as ET

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def read_students(path):
    with zipfile.ZipFile(path) as archive:
        strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            strings = [''.join(e.itertext()) for e in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('m:si', NS)]
        root = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
        rows = []
        for row in root.findall('m:sheetData/m:row', NS):
            values = {}
            for cell in row.findall('m:c', NS):
                col = re.sub(r'\d', '', cell.attrib['r'])
                value = cell.findtext('m:v', '', NS)
                if cell.get('t') == 's':
                    value = strings[int(value)]
                elif cell.get('t') == 'inlineStr':
                    value = ''.join(cell.find('m:is', NS).itertext())
                values[col] = value.strip()
            rows.append((row.attrib['r'], values))
    if not rows:
        raise ValueError('Workbook is empty')
    headers = rows[0][1]
    expected = ['student name', 'student parent no', 'maths', 'uhv', 'dbms', 'coa']
    if [headers.get(c, '').lower() for c in 'ABCDEF'] != expected:
        raise ValueError('Expected columns: Student name, Student parent no, maths, uhv, dbms, coa')
    students = []
    for row_number, row in rows[1:]:
        if not row.get('A'):
            continue
        marks = {}
        for column in 'CDEF':
            raw = row.get(column, '')
            marks[headers[column].upper()] = float(raw) if raw else None
        warnings = []
        if row['A'].lower() == 'coordinator':
            warnings.append('Confirm whether “coordinator” is a student or a test record.')
        if any(v is not None and v > 100 for v in marks.values()):
            warnings.append('A mark exceeds 100. The workbook does not specify maximum marks; verify before sending.')
        if any(v is None for v in marks.values()):
            warnings.append('Some marks are missing.')
        students.append({'id': 'row-' + row_number, 'name': row['A'], 'phone': row.get('B', ''), 'marks': marks, 'warnings': warnings})
    return students
