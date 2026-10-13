import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import therion_kontrola as app

class AltitudeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        app.ROOT=Path(self.temp.name);self.p=app.ROOT/'a.th2'
    def write(self,body):self.p.write_text('scrap s\n'+body+'endscrap\n',encoding='utf-8')
    def finding(self,kind):return [f for f in app.scan()['findings'] if f['kind']==kind]
    def test_reverse_keeps_altitude_on_its_original_coordinate(self):
        self.write('line wall -reverse on\n  0 0\n  altitude 100\n  10 0\n  altitude [fix 1510 m]\n  20 0\n  altitude .\nendline\n')
        f=self.finding('reverse')[0];self.assertTrue(f['safe'],f['reason'])
        app.apply_fixes([f['id']]);s=self.p.read_text()
        self.assertIn('  20 0\n  altitude .\n  10 0\n  altitude [fix 1510 m]\n  0 0\n  altitude 100\n',s)
        self.assertNotIn('-reverse on',s)
    def test_merge_retains_internal_altitude(self):
        self.write('line wall\n  0 0\n  10 0\n  altitude 5\n  20 0\nendline\nline wall\n  20 0\n  30 0\n  altitude 7\nendline\n')
        f=self.finding('merge')[0];self.assertTrue(f['safe'],f['reason'])
        app.apply_fixes([f['id']]);s=self.p.read_text()
        self.assertEqual(s.count('altitude'),2)
        self.assertIn('  10 0\n  altitude 5\n  20 0\n  30 0\n  altitude 7',s)
    def test_merge_retains_altitude_of_discarded_start(self):
        self.write('line wall\n  0 0\n  20 0\nendline\nline wall\n  20 0\n  altitude 33\n  30 0\nendline\n')
        f=self.finding('merge')[0];self.assertTrue(f['safe'],f['reason'])
        app.apply_fixes([f['id']]);self.assertIn('  20 0\n  altitude 33\n  30 0',self.p.read_text())
    def test_two_altitudes_conflict(self):
        self.write('line wall\n  0 0\n  20 0\n  altitude 25\nendline\nline wall\n  20 0\n  altitude 33\n  30 0\nendline\n')
        f=self.finding('merge')[0];self.assertFalse(f['safe']);self.assertIn('altitude',f['reason'])
    def test_same_altitude_not_duplicated(self):
        self.write('line wall\n  0 0\n  20 0\n  altitude 25\nendline\nline wall\n  20 0\n  altitude 25\n  30 0\nendline\n')
        f=self.finding('merge')[0];self.assertTrue(f['safe'],f['reason'])
        app.apply_fixes([f['id']]);self.assertEqual(self.p.read_text().count('altitude 25'),1)
    def test_near_start_with_altitude_requires_review(self):
        self.write('line wall\n  0 0\n  20 0\nendline\nline wall\n  20.1 0\n  altitude 25\n  30 0\nendline\n')
        f=self.finding('near')[0];self.assertFalse(f['safe']);self.assertIn('altitude',f['reason'])
    def test_smooth_and_altitude_in_reverse(self):
        self.write('line wall -reverse on\n  0 0\n  10 0\n  smooth off\n  altitude 55\n  20 0\nendline\n')
        f=self.finding('reverse')[0];self.assertTrue(f['safe'],f['reason'])
        app.apply_fixes([f['id']]);s=self.p.read_text()
        self.assertIn('  10 0\n  smooth off\n  altitude 55\n  0 0',s)
if __name__=='__main__':unittest.main()
