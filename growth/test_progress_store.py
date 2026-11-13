import tempfile, unittest
from pathlib import Path
import progress_store as p
class TestStore(unittest.TestCase):
 def test_restore_and_protect(self):
  old=p.ROOT
  with tempfile.TemporaryDirectory() as d:
   try:
    p.ROOT=Path(d)
    data={'version':1,'done':{'a':{'coins':20}},'seasonOne':{'choices':{'0':0}}}
    rev=p.write(data,'none');self.assertEqual(p.read(),data)
    with self.assertRaises(ValueError):p.write({'version':1,'done':{}},rev)
    with self.assertRaises(ValueError):p.write(data,'outdated')
    newer={**data,'theme':'rose'};p.write(newer,rev)
    self.assertEqual(p.read(),newer);self.assertEqual(len(list((p.ROOT/'history').glob('*.json'))),1)
   finally:p.ROOT=old
if __name__=='__main__':unittest.main()
