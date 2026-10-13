import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import therion_kontrola as app

class Version10Tests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        app.ROOT=Path(self.t.name);app.NEAR=1.0
    def write(self,name,body):
        p=app.ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body,encoding='utf-8');return p
    def test_internal_smooth_preserved_in_merge(self):
        p=self.write('a.th2','''scrap s
line wall -reverse on -subtype presumed
 0 0
 10 0
 smooth off
 20 0
endline
line wall -subtype presumed -reverse on
 20 0
 30 0
 smooth off
 40 0
endline
endscrap
''')
        findings=app.scan()['findings'];joins=[f for f in findings if f['kind']=='merge'];self.assertEqual(len(joins),1)
        self.assertTrue(joins[0]['safe'],joins[0]['blockers'])
        app.apply_fixes([joins[0]['id']])
        result=p.read_text();self.assertEqual(result.count('line wall'),1)
        self.assertEqual(result.count('smooth off'),2)
        self.assertEqual(result.count(' 20 0\n'),1)
        self.assertTrue(list((app.ROOT/'_Therion_zalohy').rglob('a.th2')))
    def test_smooth_at_second_line_initial_anchor_blocks(self):
        self.write('a.th2','''scrap s
line wall
 0 0
 10 0
endline
line wall
 10 0
 smooth off
 20 0
endline
endscrap
''')
        f=[x for x in app.scan()['findings'] if x['kind']=='merge'][0]
        self.assertFalse(f['safe']);self.assertIn('prvního bodu',' '.join(f['blockers']))
    def test_id_ref_index_area_join_and_no_automatic_edit(self):
        p=self.write('a.th2','''scrap s
line wall -id wall-a
 0 0
 10 0
endline
line wall
 10 0
 20 0
endline
area water
 wall-a
endarea
endscrap
''')
        self.write('references/other.th','join wall-a another-line\n')
        self.write('zaloha/unused.th','join wall-a ignored\n')
        f=[x for x in app.scan()['findings'] if x['kind']=='merge'][0]
        self.assertFalse(f['safe']);self.assertEqual(len(app.find_id_references(app.ROOT,'wall-a')),2)
        self.assertTrue(any('references/other.th' in x for x in f['blockers']))
        self.assertTrue(any('a.th2' in x for x in f['blockers']))
        before=p.read_bytes()
        with self.assertRaises(ValueError):app.apply_fixes([f['id']])
        self.assertEqual(p.read_bytes(),before)
if __name__=='__main__':unittest.main()
