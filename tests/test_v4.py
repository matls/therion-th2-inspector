import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import therion_kontrola as app

class V4Tests(unittest.TestCase):
    def test_reverse_source_order_and_smooth(self):
        with tempfile.TemporaryDirectory() as td:
            app.ROOT=Path(td)
            source='''scrap s
line floor-step
 10 0
 12 0 13 0 15 0
 smooth off
 20 0
endline
line wall
 1 1
 1 3
endline
line floor-step
 0 0
 smooth off
 10 0
endline
endscrap
'''
            p=app.ROOT/'drawing.th2';p.write_text(source)
            fs=app.scan()['findings'];joins=[f for f in fs if f['kind']=='merge' and f['safe']]
            self.assertEqual(len(joins),1)
            app.apply_fixes([joins[0]['id']]);result=p.read_text()
            self.assertEqual(result.count('line floor-step'),1)
            self.assertIn(' 12 0 13 0 15 0',result)
            self.assertIn('line wall',result)
            self.assertEqual(result.count('endline'),2)
            self.assertEqual(result.count(' 10 0\n'),1)
            self.assertTrue(list((app.ROOT/'_Therion_zalohy').rglob('drawing.th2')))
    def test_small_bezier_loop_can_be_removed(self):
        with tempfile.TemporaryDirectory() as td:
            app.ROOT=Path(td)
            p=app.ROOT/'drawing.th2'
            p.write_text('''scrap s
line wall
 0 0
 8 0 10 0 10 10
 12 12 9 9 10 10
 smooth off
endline
endscrap
''')
            fs=app.scan()['findings'];dup=[f for f in fs if f['kind']=='dup']
            self.assertEqual(len(dup),1)
            self.assertTrue(dup[0]['safe'])
            app.apply_fixes([dup[0]['id']])
            self.assertNotIn('12 12 9 9 10 10',p.read_text())
    def test_large_bezier_loop_requires_review(self):
        with tempfile.TemporaryDirectory() as td:
            app.ROOT=Path(td)
            p=app.ROOT/'drawing.th2'
            p.write_text('''scrap s
line wall
 0 0
 10 10
 90 90 80 80 10 10
endline
endscrap
''')
            d=[x for x in app.scan()['findings'] if x['kind']=='dup']
            self.assertFalse(d[0]['safe'])

if __name__=='__main__':unittest.main()
