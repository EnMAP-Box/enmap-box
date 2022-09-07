from unittest import TestCase

from enmapboxprocessing.glossary import injectGlossaryLinks


class TestUtils(TestCase):

    def test_LinearSVC_issue(self):
        text = 'Training dataset pickle file used for fitting the classifier. If not specified, an unfitted classifier is created.'
        lead = injectGlossaryLinks(text)
        # self.assertEqual(gold, lead)

        # self.assertEqual(white, Utils.parseColor('255, 255, 255'))

    def test_weblinkWithGlossaryTermConflict(self):  # adresses issue #741
        # term "classification" inside the weblink shouldn't be replaced
        text = 'Used in the Cookbook Recipes: <a href="https://classification.html">Classification</a>,'
        text2 = injectGlossaryLinks(text)
        self.assertEqual(text, text2)

    def test_injectTerm_feature(self):
        text = 'abc feature def'
        text2 = injectGlossaryLinks(text)
        self.assertEqual(
            text2,
            'abc <a href="https://enmap-box.readthedocs.io/en/latest/general/glossary.html#term-feature">feature</a> def'
        )

    def test_injectTerm_features(self):
        text = 'abc features def'
        text2 = injectGlossaryLinks(text)
        self.assertEqual(
            text2,
            'abc <a href="https://enmap-box.readthedocs.io/en/latest/general/glossary.html#term-feature">features</a> def'
        )
