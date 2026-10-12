import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import therion_kontrola as app

class V7Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        app.ROOT=Path(self.tmp.name)
        self.p=app.ROOT/'test.th2'

    def test_chain_out_of_source_order_with_interleaved_other_lines(self):
        self.p.write_text('''scrap s
line wall
 10 0
 20 0
endline
line rock-border
 5 5
 6 6
endline
line wall
 20 0
 25 1 28 0 30 0
endline
line wall
 0 0
 10 0
endline
endscrap
''')
        findings=app.scan()['findings']
        chains=[x for x in findings if x['kind']=='chain']
        self.assertEqual(len(chains),1)
        chain=chains[0]
        self.assertEqual(len(chain['chain_keys']),3)
        self.assertTrue(chain['safe'])
        a,b=[x for x in findings if x['kind']=='merge' and x['safe']]
        with self.assertRaisesRegex(ValueError,'Konfliktní'):
            app.apply_fixes([chain['id'],a['id']])
        self.assertEqual(self.p.read_text().count('line wall'),3)
        result=app.apply_fixes([chain['id']])
        output=self.p.read_text()
        self.assertEqual(output.count('line wall'),1)
        self.assertEqual(output.count('line rock-border'),1)
        self.assertIn('25 1 28 0 30 0',output)
        self.assertLess(output.index(' 0 0'),output.index(' 10 0'))
        self.assertLess(output.index(' 10 0'),output.index(' 20 0'))
        self.assertLess(output.index(' 20 0'),output.index('25 1 28 0 30 0'))
        self.assertEqual(result['slouceno_retezcu'],1)
        self.assertEqual(len(list((app.ROOT/'_Therion_zalohy').rglob('test.th2'))),1)

    def test_different_attributes_prevent_chain(self):
        self.p.write_text('''scrap s
line wall
 0 0
 10 0
endline
line wall -outline none
 10 0
 20 0
endline
line wall
 20 0
 30 0
endline
endscrap
''')
        findings=app.scan()['findings']
        self.assertFalse(any(f['kind']=='chain' for f in findings))

    def test_branch_prevents_automatic_chain(self):
        self.p.write_text('''scrap s
line wall
 0 0
 10 0
endline
line wall
 10 0
 20 0
endline
line wall
 10 0
 20 10
endline
line wall
 20 0
 30 0
endline
endscrap
''')
        findings=app.scan()['findings']
        self.assertFalse(any(f['kind']=='chain' for f in findings))

    def test_independent_merges_same_batch(self):
        self.p.write_text('''scrap s
line wall
 0 0
 10 0
endline
line wall
 10 0
 20 0
endline
line wall
 40 0
 50 0
endline
line wall
 50 0
 60 0
endline
endscrap
''')
        finds=app.scan()['findings']
        merges=[f['id'] for f in finds if f['kind']=='merge' and f['safe']]
        self.assertEqual(len(merges),2)
        app.apply_fixes(merges)
        self.assertEqual(self.p.read_text().count('line wall'),2)

if __name__=='__main__': unittest.main()