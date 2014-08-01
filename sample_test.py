"""
This file exists to demonstrate the functionality of 
FlaskCI. It doesn't test the apps functionality - I'm not 
sure how you would test a CI engine?
"""
import unittest

class Test(unittest.TestCase):

    def test_foo(self):
        print 'test foo, successful'

    def test_bar(self):
        print 'test foo, bar: fails'
        raise Exception('bar error')


if __name__ == '__main__':
    unittest.main()