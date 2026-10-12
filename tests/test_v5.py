import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import therion_kontrola as app

class VersionFiveTests(unittest.TestCase):
    def test_merge_is_advisory_and_api_rejects_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            app.ROOT=Path(tmp)
            p=app.ROOT/'example.th2'
            original='''scrap S
line floor-step
 0 0
 10 0
endline
line floor-step
 10 0
 20 0
endline
endscrap
'''
            p.write_text(original)
            findings=app.scan()['findings']
            merges=[f for f in findings if f['kind']=='merge']
            self.assertEqual(len(merges),1)
            self.assertFalse(merges[0]['safe'])
            with self.assertRaisesRegex(ValueError,'ruční'):
                app.apply_fixes([merges[0]['id']])
            self.assertEqual(p.read_text(),original)
            self.assertFalse((app.ROOT/'_Therion_zalohy').exists())
    def test_regular_edits_remain_enabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            app.ROOT=Path(tmp)
            p=app.ROOT/'example.th2'
            p.write_text('''scrap S
line pit -close off
 0 0
 10 0
 0 0
endline
endscrap
''')
            fs=app.scan()['findings']
            closes=[x for x in fs if x['kind']=='open']
            self.assertEqual(len(closes),1)
            self.assertTrue(closes[0]['safe'])
            app.apply_fixes([closes[0]['id']])
            self.assertIn('-close on',p.read_text())
            self.assertTrue((app.ROOT/'_Therion_zalohy').exists())
if __name__=='__main__':unittest.main()
