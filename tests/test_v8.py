import tempfile,unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import therion_kontrola as app
class V8Tests(unittest.TestCase):
 def run_case(self,body):
  return tempfile.TemporaryDirectory()
 def test_reverse_subtype_different_order(self):
  with tempfile.TemporaryDirectory() as tmp:
   app.ROOT=Path(tmp);p=app.ROOT/'a.th2'
   p.write_text('''scrap A
line wall -reverse on -subtype bedrock
 0 0
 10 0
endline
line wall -subtype bedrock -reverse on
 10 0
 20 0
endline
endscrap
''')
   m=[f for f in app.scan()['findings'] if f['kind']=='merge']
   self.assertEqual(len(m),1);self.assertTrue(m[0]['safe'])
   app.apply_fixes([m[0]['id']])
   self.assertEqual(p.read_text().count('line wall'),1)
   self.assertIn('line wall -reverse on -subtype bedrock',p.read_text())
 def test_near_end_bezier_control_points_unchanged(self):
  with tempfile.TemporaryDirectory() as tmp:
   app.ROOT=Path(tmp);p=app.ROOT/'a.th2'
   p.write_text('''scrap A
line wall -reverse on
 0 0
 10 0
endline
line wall -reverse on
 10.3 0.4
 12 4 15 4 20 5
endline
endscrap
''')
   f=[x for x in app.scan()['findings'] if x['kind']=='near']
   self.assertEqual(len(f),1);self.assertTrue(f[0]['safe'])
   app.apply_fixes([f[0]['id']]);out=p.read_text()
   self.assertEqual(out.count('line wall'),1)
   self.assertNotIn(' 10.3 0.4',out)
   self.assertIn(' 12 4 15 4 20 5',out)
   self.assertIn(' 10 0\n 12 4',out)
 def test_mismatched_subtype_blocks(self):
  with tempfile.TemporaryDirectory() as tmp:
   app.ROOT=Path(tmp);p=app.ROOT/'a.th2'
   p.write_text('''scrap A
line wall -subtype bedrock
 0 0
 10 0
endline
line wall -subtype presumed
 10 0
 20 0
endline
endscrap
''')
   m=[x for x in app.scan()['findings'] if x['kind']=='merge']
   self.assertEqual(len(m),1);self.assertFalse(m[0]['safe'])
 def test_close_wall_with_matching_first_last(self):
  with tempfile.TemporaryDirectory() as tmp:
   app.ROOT=Path(tmp);p=app.ROOT/'a.th2'
   p.write_text('''scrap A
line wall
 0 0
 10 0
 10 10
 0 0
endline
endscrap
''')
   fs=app.scan()['findings']
   self.assertEqual(len([f for f in fs if f['kind']=='dup']),0)
   c=[f for f in fs if f['kind']=='open'];self.assertEqual(len(c),1)
   app.apply_fixes([c[0]['id']]);self.assertIn('-close on',p.read_text())
 def test_skip_dirs_show_header(self):
  with tempfile.TemporaryDirectory() as tmp:
   app.ROOT=Path(tmp)
   for name in ('Data','Záloha','zaloha','_Therion_zalohy'):
    folder=app.ROOT/name;folder.mkdir();(folder/'fake.th2').write_text('scrap S\nendscrap\n')
   (app.ROOT/'good.th2').write_text('scrap S\nendscrap\n')
   data=app.scan()
   self.assertEqual(data['files'],1)
   self.assertIn('záloha',data['excluded_folders'])
   self.assertIn('id="excluded"',app.HTML)
 def test_chain_near_and_exact(self):
  with tempfile.TemporaryDirectory() as tmp:
   app.ROOT=Path(tmp);p=app.ROOT/'a.th2'
   p.write_text('''scrap A
line wall
 10.2 0
 20 0
endline
line wall
 20 0
 30 0
endline
line wall
 0 0
 10 0
endline
endscrap
''')
   fs=app.scan()['findings'];ch=[x for x in fs if x['kind']=='chain']
   self.assertEqual(len(ch),1);self.assertTrue(ch[0]['safe'])
   app.apply_fixes([ch[0]['id']]);self.assertEqual(p.read_text().count('line wall'),1)
   self.assertIn(' 0 0\n 10 0\n 20 0\n 30 0',p.read_text())
if __name__=='__main__':unittest.main()