#!/usr/bin/env python
# vi: ts=4 sw=4 sts=4 et ft=python
# global
import traceback
import os
import sys
import unittest
import logging
import pprint
import shutil
import platform

# module-level logger
logger = logging.getLogger(__name__)

# module-global test-specific imports
# where to put test output data for compare.
testdatadir = os.path.join('.', 'test', 'test_data')
rawdata_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
testfiles = (
    'bogus.data',
)
purge_results = False
output_dir = os.path.join('test_data', 'example_out')


def cleanPath(path):
    '''cleanPath
    Recursively removes everything below a path

    :param path:
    the path to clean
    '''
    for root, files, dirs in os.walk(path):
        for fn in files:
            logger.debug('removing {}'.format(fn))
            os.unlink(os.path.join(root, fn))
        for dn in dirs:
            # recursive
            try:
                logger.debug('recursive del {}'.format(dn))
                shutil.removedirs(dn)
            except Exception as err:
                # for now, halt on all.  Override with shutil onerror
                # callback and ignore_errors.
                raise


class TestSciTools(unittest.TestCase):
    '''
        TestSciTools
    '''
    testdatadir = None
    rawdata_dir = None
    testfiles   = None
    output_dir  = output_dir

    def __init__(self, *args, **kwargs):
        self.testdatadir = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), testdatadir)
        super(TestSciTools, self).__init__(*args, **kwargs)
        # check for kwargs
        # this allows test control by instance
        self.testdatadir = kwargs.get('testdatadir', testdatadir)
        self.rawdata_dir = kwargs.get('rawdata_dir', rawdata_dir)
        self.testfiles = kwargs.get('testfiles', testfiles)
        self.output_dir = kwargs.get('output_dir', output_dir)

    def setUp(self):
        '''setUp
        pre-test setup called before each test
        '''
        logging.debug('setUp')
        if not os.path.exists(self.testdatadir):
            os.mkdir(self.testdatadir)
        else:
            self.assertTrue(os.path.isdir(self.testdatadir))
        self.assertTrue(os.path.exists(self.testdatadir))
        cleanPath(self.output_dir)

    def tearDown(self):
        '''tearDown
        post-test cleanup, if required
        '''
        logging.debug('tearDown')
        if purge_results:
            cleanPath(self.output_dir)

    def darwin_envtest(self):
        """darwin_envtest
        stub, does nothing right now.
        """
        # let's start by making sure that texbin is in the path.
        self.failUnless(os.environ['PATH'].find('texbin') > 0)

    def empty_envtest(self):
        """empty_envtest
        stub, does nothing right now.
        """
        pass

    def test_environ_0(self):
        '''test_environ_0
            Check the current os-dependent environment for missing stuff.
        '''
        env_tests = {
            'Linux'   : self.empty_envtest,
            'Windows' : self.empty_envtest,
            'Darwin'  : self.darwin_envtest,
        }
        env_tests[platform.system()]()

    def default_test(self):
        ''' default_test
        Tests all data files for type and compares the results to the current
        stored results.
        '''
        self.test_environ_0()
        try:
            import numpy as np
            from numpy import cos, pi
            import matplotlib as mpl
            import matplotlib.pyplot as plt
            mpl.rc('text', usetex = True)
            mpl.rc('font', family = 'serif')
            plt.figure(1, figsize = (6, 4))
            # ax = plt.axes([0.1, 0.1, 0.8, 0.7])
            t = np.arange(0.0, 1.0+0.01, 0.01)
            s = cos(2*2*pi*t)+2
            plt.plot(t, s)

            plt.xlabel(r'\textbf{time (s)}')
            plt.ylabel(r'\textit{voltage (mV)}', fontsize = 16)
            plt.title(
                r"\TeX\ is Number $\displaystyle\sum_{n=1}" +
                r"^\infty\frac{-e^{i\pi}}{2^n}$!",
                fontsize = 16, color = 'r')
            plt.grid(True)
            plt.savefig(os.path.join(self.output_dir, 'tex_demo'))
            # don't do this during test
            # plt.show()
        except ImportError as ie:
            traceback.print_exc()
            self.fail('unable to import matplotlib:')


# stand-alone test execution
if __name__ == '__main__':
    import nose2
    nose2.main(
        argv=[
            'fake',
            '--log-capture',
            'TestSciTools.default_test',
        ])
