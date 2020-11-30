import unittest

from backend.text_formatter import CodeTextFormatter

class TestTextWriterBasics(unittest.TestCase):
    """Test basic text formatter stuff"""

    def setUp(self):
        self.formatter = CodeTextFormatter()

    def test_fix_closures_double_quote(self):
        """Test closures with double quotes"""
        the_text = 'what " the blah " hey donkey " blood "'
        out_expect = 'what "the blah" hey donkey "blood"'
        out = self.formatter.fix_closures(the_text)
        self.assertEqual(out, out_expect)

    def test_fix_closures_single_quote(self):
        """Test closures with single quotes"""
        the_text = "what ' the blah ' hey donkey ' blood '"
        out_expect = "what 'the blah' hey donkey 'blood'"
        out = self.formatter.fix_closures(the_text)
        self.assertEqual(out, out_expect)
    
    def test_fix_closures_backtick(self):
        """Test closures with backticks"""
        the_text = "what ` the blah ` hey donkey ` blood `"
        out_expect = "what `the blah` hey donkey `blood`"
        out = self.formatter.fix_closures(the_text)
        self.assertEqual(out, out_expect)
    
    def test_fix_closures_parentheses(self):
        """Test closures with parentheses"""
        the_text = "what ( the blah ( hey donkey ) blood )"
        out_expect = "what(the blah(hey donkey)blood)"
        out = self.formatter.fix_closures(the_text)
        self.assertEqual(out, out_expect)
    
if __name__ == '__main__':
    unittest.main()