#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_cdlouvain
----------------------------------

Tests for `cdlouvain` module.
"""

import os
import sys
import unittest
import tempfile
import shutil


from cdlouvain import cdlouvaincmd


class TestCdlouvain(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_parse_args(self):
        myargs = ['inputarg']
        res = cdlouvaincmd._parse_arguments('desc', myargs)
        self.assertEqual('inputarg', res.input)
        self.assertEqual('RB', res.configmodel)
        self.assertEqual(0.1, res.resolution_parameter)

    def test_run_louvain_no_file(self):
        temp_dir = tempfile.mkdtemp()
        try:
            tfile = os.path.join(temp_dir, 'foo')
            myargs = [tfile]
            theargs = cdlouvaincmd._parse_arguments('desc', myargs)
            res = cdlouvaincmd.run_louvain(tfile, theargs)
            self.assertEqual(3, res)
        finally:
            shutil.rmtree(temp_dir)

    def test_run_louvain_empty_file(self):
        temp_dir = tempfile.mkdtemp()
        try:
            tfile = os.path.join(temp_dir, 'foo')
            open(tfile, 'a').close()
            myargs = [tfile]
            theargs = cdlouvaincmd._parse_arguments('desc', myargs)
            res = cdlouvaincmd.run_louvain(tfile, theargs)
            self.assertEqual(4, res)
        finally:
            shutil.rmtree(temp_dir)

    def test_main_invalid_file(self):
        temp_dir = tempfile.mkdtemp()
        try:
            tfile = os.path.join(temp_dir, 'foo')
            myargs = ['prog', tfile]
            res = cdlouvaincmd.main(myargs)
            self.assertEqual(3, res)
        finally:
            shutil.rmtree(temp_dir)

    def test_main_empty_file(self):
        temp_dir = tempfile.mkdtemp()
        try:
            tfile = os.path.join(temp_dir, 'foo')
            open(tfile, 'a').close()
            myargs = ['prog', tfile]
            res = cdlouvaincmd.main(myargs)
            self.assertEqual(4, res)
        finally:
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    sys.exit(unittest.main())
