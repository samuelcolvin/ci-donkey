"""
This file exists to demonstrate the functionality of 
FlaskCI. It doesn't test the apps functionality - I'm not 
sure how you would test a CI engine?
"""
import unittest

class Test(unittest.TestCase):

    def test_bar(self):
        print 'test bar, successful'

    def test_foo(self):
        print 'test foo: fails'
        # raise Exception('foo error')


if __name__ == '__main__':
    unittest.main()