import unittest

from backend.commands import CaseCmdExec

class TestCaseCmdFormatCase(unittest.TestCase):
    """Test basic case formatting"""

    def test_upper(self):
        """Test upper case"""
        the_text = "slim shady foo"
        out_expect = "SLIM SHADY FOO"
        out = CaseCmdExec.format_case(the_text, 'upper')
        self.assertEqual(out, out_expect)
    
    def test_lower(self):
        """Test lower case"""
        the_text = "slim shady foo"
        out_expect = "slim shady foo"
        out = CaseCmdExec.format_case(the_text, 'lower')
        self.assertEqual(out, out_expect)
    
    def test_title(self):
        """Test title case"""
        the_text = "slim shady foo"
        out_expect = "Slim Shady Foo"
        out = CaseCmdExec.format_case(the_text, 'title')
        self.assertEqual(out, out_expect)
    
    def test_snake(self):
        """Test snake case"""
        the_text = "slim shady foo"
        out_expect = "slim_shady_foo"
        out = CaseCmdExec.format_case(the_text, 'snake')
        self.assertEqual(out, out_expect)
    
    def test_screaming_snake(self):
        """Test screaming_snake case"""
        the_text = "slim shady foo"
        out_expect = "SLIM_SHADY_FOO"
        out = CaseCmdExec.format_case(the_text, 'screaming snake')
        self.assertEqual(out, out_expect)
    
    def test_camel(self):
        """Test camel case"""
        the_text = "slim shady foo"
        out_expect = "slimShadyFoo"
        out = CaseCmdExec.format_case(the_text, 'camel')
        self.assertEqual(out, out_expect)
    
if __name__ == '__main__':
    unittest.main()