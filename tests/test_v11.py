import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import therion_kontrola as app

class Version11Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        app.ROOT=Path(self.tmp.name)
    def create(self,typ='wall',reverse=True,idstr='',mid=''):
        header=f'line {typ}'+(' -reverse on' if reverse else '')+(' -id x' if idstr else '')
        content=f'''scrap s
{header}
  0 0
  15 30 35 30 50 0
{mid}  70 0
  80 -10 90 -10 100 0
endline
endscrap
'''
        p=app.ROOT/'a.th2';p.write_text(content)
        return p
    def reverse(self):
        return [f for f in app.scan()['findings'] if f['kind']=='reverse']
    def test_reverses_beziers_exactly_for_supported_types(self):
        for typ in ('wall','slope','pit','chimney','floor-step'):
            with self.subTest(typ=typ):
                p=self.create(typ)
                found=self.reverse();self.assertEqual(len(found),1)
                self.assertTrue(found[0]['safe'],found[0]['reason'])
                before=app.parse_file(p)['shapes'][0]['segments']
                app.apply_fixes([found[0]['id']])
                result=p.read_text();self.assertNotIn('-reverse on',result)
                after=app.parse_file(p)['shapes'][0]['segments']
                self.assertEqual([seg['points'] for seg in after], [list(reversed(seg['points'])) for seg in reversed(before)])
                self.assertTrue(list((app.ROOT/'_Therion_zalohy').rglob('a.th2')))
    def test_normal_wall_and_border_untouched(self):
        p=self.create(reverse=False);self.assertFalse(self.reverse());self.assertIn('line wall',p.read_text())
        p=self.create(typ='border');self.assertFalse(self.reverse())
    def test_id_is_not_automatic(self):
        self.create(idstr='x');reversals=self.reverse();self.assertEqual(len(reversals),1)
        self.assertFalse(reversals[0]['safe']);self.assertIn('ID',reversals[0]['reason'])
    def test_internal_smooth_preserved(self):
        p=self.create(mid='  smooth off\n')
        f=self.reverse()[0];self.assertTrue(f['safe'],f['reason'])
        app.apply_fixes([f['id']]);self.assertEqual(p.read_text().count('smooth off'),1)
        self.assertIn('  50 0\n  smooth off\n  35 30 15 30 0 0',p.read_text())
    def test_smooth_endpoint_requires_review(self):
        self.create(mid='  smooth on\n')
        # smooth attached to the previous anchor is internal, safe
        self.assertTrue(self.reverse()[0]['safe'])
        p=app.ROOT/'a.th2';p.write_text('scrap s\nline wall -reverse on\n  0 0\n  smooth off\n  10 0\nendline\nendscrap\n')
        self.assertFalse(self.reverse()[0]['safe'])
    def test_two_stage_reversal_enables_join(self):
        p=app.ROOT/'a.th2'
        p.write_text('''scrap s
line wall
  0 0
  10 0
endline
line wall -reverse on
  20 0
  10 0
endline
endscrap
''')
        r=self.reverse();self.assertTrue(r[0]['safe'])
        app.apply_fixes([r[0]['id']]);self.assertEqual(len([f for f in app.scan()['findings'] if f['kind']=='merge' and f['safe']]),1)
