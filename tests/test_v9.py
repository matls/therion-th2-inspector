import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import therion_kontrola as app

class V9Diagnostics(unittest.TestCase):
 def findings(self,first,second):
  with tempfile.TemporaryDirectory() as tmp:
   app.ROOT=Path(tmp)
   p=app.ROOT/'t.th2'
   p.write_text('scrap S\n'+first+second+'endscrap\n',encoding='utf-8')
   return [f for f in app.scan()['findings'] if f['kind']=='merge']
 def test_mismatched_named_options(self):
  r=self.findings('line wall -subtype bedrock -reverse on\n 0 0\n 10 0\nendline\n','line wall -reverse off -subtype presumed\n 10 0\n 20 0\nendline\n')
  self.assertEqual(len(r),1)
  self.assertFalse(r[0]['safe'])
  self.assertTrue(any('-reverse' in x and 'on' in x and 'off' in x for x in r[0]['blockers']))
  self.assertTrue(any('-subtype' in x and 'bedrock' in x and 'presumed' in x for x in r[0]['blockers']))
 def test_id_and_internal_directive_reasons(self):
  r=self.findings('line wall -id a\n 0 0\n smooth off\n 10 0\nendline\n','line wall\n 10 0\n 20 0\nendline\n')
  self.assertEqual(len(r),1)
  self.assertTrue(any('ID' in x for x in r[0]['blockers']))
  self.assertTrue(any('smooth off' in x for x in r[0]['blockers']))
 def test_safe_join_has_no_blockers(self):
  r=self.findings('line wall -reverse on\n 0 0\n 10 0\nendline\n','line wall -reverse on\n 10 0\n 20 0\nendline\n')
  self.assertTrue(r[0]['safe'])
  self.assertEqual(r[0]['blockers'],[])
 def test_header_blockers_are_rendered(self):
  self.assertIn('id="blockers"',app.HTML)
  self.assertIn('Proč nelze sloučit automaticky:',app.HTML)
if __name__=='__main__': unittest.main()