"""
Tests of enmapbox.typeguard module
"""
import unittest

from enmapbox.testing import EnMAPBoxTestCase


class TestCaseIssue345(EnMAPBoxTestCase):
    try:
        import typeguard
        IS_INSTALLED = True
    except (ImportError, ModuleNotFoundError):
        IS_INSTALLED = False

    def test_typeguard_on(self):

        from enmapbox.typeguard import typechecked

        @typechecked
        def mydef(value: int):
            return value

        exception = None
        try:
            mydef('wrong type')
        except TypeError as ex:
            exception = ex

        if TestCaseIssue345.IS_INSTALLED:
            self.assertIsInstance(exception, TypeError)
        else:
            self.assertTrue(exception is None)


if __name__ == '__main__':
    unittest.main(buffer=False)
