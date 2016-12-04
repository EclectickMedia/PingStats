import unittest
from hypothesis import given
from hypothesis import strategies as st
# TEST RESOURCES
from io import TextIOWrapper
import os
import csv
import PingStats


class TestCore(unittest.TestCase):
    """ Tests all non-plot related functionality. """
    @given(st.just(os.curdir), st.text())
    def test_build_files(self, path, name):
        try:
            test_file = PingStats.buildfile(path, name)
            self.assertIsInstance(test_file, TextIOWrapper)
            test_file.close()
            os.remove(test_file.name)
        except ValueError as e:
            if str(e) == 'embedded null byte':
                print('Caught embedded null byte error in test_build_files')
            else:
                raise
        except FileNotFoundError:
            print('TestCore.test_build_files caught OS non legal file path: '
                  '%s%s' % (path, name))

    @given(st.just(csv.writer(open('test.csv', 'w+'))), st.lists(st.integers(),
                                                                 min_size=2))
    def test_write_csv_data(self, writer, data):
        self.assertEqual(PingStats.write_csv_data(writer, data), data)

    @given(st.sampled_from(['google.ca', 'www.facebook.ca', '8.8.8.8']))
    def test_active_connections(self, address):
        try:
            self.assertIsInstance(PingStats.ping(address,
                                                 verbose=False).__next__()[1],
                                  float)
        except PermissionError as e:
            if e.errno == 1:
                print('Run tests as sudo')

    @given(st.text())
    def test_failed_connections(self, address):
        self.assertEqual(PingStats.ping(address, verbose=False).__next__()[1],
                         None)


if __name__ == '__main__':
    unittest.main()