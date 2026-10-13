import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import therion_kontrola as app

class V6RegressionTests(unittest.TestCase):
    def test_distant_line_merging_preserves_intervening_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            app.ROOT=Path(tmp)
            p=app.ROOT/'a.th2'
            p.write_text('''scrap A
line wall
 10 0
 20 0
endline
line pit
 70 70
 80 80
endline
line wall
 0 0
 10 0
endline
endscrap
''')
            findings=app.scan()['findings']
            m=[x for x in findings if x['kind']=='merge' and x['safe']]
            self.assertEqual(len(m),1)
            app.apply_fixes([m[0]['id']])
            result=p.read_text()
            self.assertEqual(result.count('line wall'),1)
            self.assertIn('line pit',result)
            self.assertIn(' 0 0\n 10 0\n 20 0\n',result)
            self.assertEqual(result.count('endline'),2)
    def test_reverse_and_inside_directives_not_auto_mergable(self):
        # Identical -reverse is now supported; internal directives remain blocked.
        with tempfile.TemporaryDirectory() as tmp:
            app.ROOT=Path(tmp);p=app.ROOT/'a.th2'
            p.write_text("""scrap A
line wall -reverse on
 0 0
 10 0
endline
line wall -reverse on
 10 0
 20 0
endline
endscrap
""")
            f=[x for x in app.scan()['findings'] if x['kind']=='merge']
            self.assertEqual(len(f),1)
            self.assertTrue(f[0]['safe'])
            app.apply_fixes([f[0]['id']])
            self.assertEqual(p.read_text().count('line wall -reverse on'),1)
        with tempfile.TemporaryDirectory() as tmp:
            app.ROOT=Path(tmp);p=app.ROOT/'a.th2'
            p.write_text('''scrap A
line wall
 0 0
 10 0
 smooth off
endline
line wall
 10 0
 20 0
endline
endscrap
''')
            f=[x for x in app.scan()['findings'] if x['kind']=='merge']
            self.assertEqual(len(f),1);self.assertFalse(f[0]['safe'])
    def test_straight_duplicate_after_bezier(self):
        with tempfile.TemporaryDirectory() as tmp:
            app.ROOT=Path(tmp);p=app.ROOT/'a.th2'
            p.write_text('''scrap A
line wall
 0 0
 2 3 3 4 10 10
 10 10
 20 20
endline
endscrap
''')
            fs=[f for f in app.scan()['findings'] if f['kind']=='dup']
            self.assertEqual(len(fs),1);self.assertTrue(fs[0]['safe'])
            app.apply_fixes([fs[0]['id']]);out=p.read_text()
            self.assertIn(' 2 3 3 4 10 10',out)
            self.assertNotIn('\n 10 10\n',out)
    def test_real_skareda_loop_proposal_preserves_endpoints(self):
        p=Path('/mnt/data/Skareda_chodba_23.1.21_PLAN.th2')
        if not p.exists():self.skipTest('Fixture not present')
        app.ROOT=p.parent
        findings=app.scan()['findings']
        matches=[f for f in findings if f['kind']=='loop' and f['row']==1399]
        self.assertTrue(matches)
        self.assertTrue(matches[0]['safe'])
        proposal=matches[0]['proposed_points']
        self.assertEqual(proposal[3],[-8477.677,-11402.699])
        self.assertFalse(app.detect(app.flatten(tuple(proposal),app.TOL)))
        with tempfile.TemporaryDirectory() as tmp:
            app.ROOT=Path(tmp)
            q=app.ROOT/p.name;q.write_bytes(p.read_bytes())
            hit=[f for f in app.scan()['findings'] if f['kind']=='loop' and f['row']==1399][0]
            app.apply_fixes([hit['id']])
            line=q.read_text().splitlines()[1398].split()
            self.assertEqual(line[-2:],['-8477.677','-11402.699'])
            self.assertNotEqual(line[:4],['-8487.125','-11414.129','-8317.5','-11311.881'])
            self.assertTrue((app.ROOT/'_Therion_zalohy').exists())
    def test_ambiguous_batch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            app.ROOT=Path(tmp);p=app.ROOT/'a.th2'
            p.write_text('''scrap A
line wall
 0 0
 10 0
endline
line wall
 10 0
 20 0
endline
line wall
 20 0
 30 0
endline
endscrap
''')
            merges=[f for f in app.scan()['findings'] if f['kind']=='merge' and f['safe']]
            self.assertEqual(len(merges),2)
            with self.assertRaises(ValueError):app.apply_fixes([m['id'] for m in merges])
            self.assertEqual(p.read_text().count('line wall'),3)

if __name__=='__main__':unittest.main()