import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from p2study.scoring import score,normalize,row_equal
class ScoringTests(unittest.TestCase):
    def test_duplicate_is_false_positive(self):
        m,_=score([[1,'A'],[1,'A']],[[1,'A']],['INTEGER','TEXT'])
        self.assertEqual((m['tp'],m['fp'],m['fn']),(1,1,0))
    def test_partial_not_true_positive(self):
        m,l=score([[1,'A','wrong']],[[1,'A','B']],['INTEGER','TEXT','TEXT'])
        self.assertEqual((m['tp'],m['fp'],m['fn'],m['partial']),(0,1,1,1))
    def test_one_gold_cannot_be_partial_twice(self):
        m,_=score([[1,'A','X'],[1,'A','Y']],[[1,'A','B']],['INTEGER','TEXT','TEXT'])
        self.assertEqual((m['partial'],m['fp']),(1,2))
    def test_complete_has_priority_over_partial(self):
        m,_=score([[1,'A','X'],[1,'A','B']],[[1,'A','B']],['INTEGER','TEXT','TEXT'])
        self.assertEqual((m['tp'],m['partial'],m['fp']),(1,0,1))
    def test_no_output_precision_undefined(self):
        m,_=score([],[[1]],['INTEGER']);self.assertIsNone(m['precision']);self.assertEqual(m['recall'],0)
    def test_real_absolute_tolerance(self):
        self.assertTrue(row_equal([1.123456],[1.12346],['REAL']))
        self.assertFalse(row_equal([1e9+1],[1e9],['REAL']))
    def test_invalid_not_dropped_and_null_not_empty(self):
        self.assertEqual(normalize('x12','INTEGER'),'x12')
        self.assertFalse(row_equal([''],[None],['TEXT']))
        m,_=score([['x12']],[[12]],['INTEGER']);self.assertEqual(m['fp'],1)
    def test_short_row_cannot_match(self):
        m,_=score([[1]],[[1,'A']],['INTEGER','TEXT']);self.assertEqual((m['tp'],m['fp']),(0,1))
if __name__=='__main__':unittest.main()
