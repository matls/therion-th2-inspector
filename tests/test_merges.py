"""Run: python -m unittest discover -s tests -v"""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
spec = importlib.util.spec_from_file_location('therion_kontrola', BASE / 'therion_kontrola.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

class MergeTests(unittest.TestCase):
    def test_exact_near_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            app.ROOT = Path(tmp)
            f = app.ROOT / 'sample.th2'
            f.write_text('''scrap test
line wall
 0 0
 10 0
endline
line wall
 10 0
 20 0
endline
line wall
 20.2 0
 30 0
endline
line pit -close off
 0 0
 5 5
 0 0
endline
endscrap
''')
            findings = app.scan()['findings']
            exact = [x for x in findings if x['kind'] == 'merge']
            self.assertEqual(len(exact), 1)
            self.assertTrue(exact[0]['safe'])
            self.assertTrue(any(x['kind'] == 'near' and not x['safe'] for x in findings))
            self.assertTrue(any(x['kind'] == 'open' for x in findings))
            app.apply_fixes([exact[0]['id']])
            self.assertEqual(f.read_text().count('line wall'), 2)
            self.assertTrue((app.ROOT / '_Therion_zalohy').exists())

if __name__ == '__main__':
    unittest.main()