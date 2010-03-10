import os
import unittest

from base import DataTable



class BaseTableTestCase(unittest.TestCase):
    def setUp(self):
        self.animals = [{'species': 'Cat', 'breed': 'American Short Hair'}, 
                        {'species': 'Cat', 'breed': 'Siamese'},
                        {'species': 'Dog', 'breed': 'Welsh Corgi'}]

    def assertFileContentsMatch(self, str, filename):
        if not filename.startswith('/'):
            filename = os.path.join(os.path.dirname(__file__), filename)
        self.assertEquals(str, open(filename, 'r').read())

    def testSimple1(self):
        t = DataTable(wrapper=False)
        t.render(self.animals, fields=('species', 'breed'))
        self.assertFileContentsMatch(t.flush(), 'test_output/simple1.html')

    def testGroup1(self):
        t = DataTable(wrapper=False)
        t.render(self.animals, fields=('species', 'breed'), group='species')
        self.assertFileContentsMatch(t.flush(), 'test_output/group1.html')


try:
    import mako
    class MakoTableTestCase(unittest.TestCase):
        pass
except ImportError:
    #print 'Mako not installed, skipping tests.'
    pass
