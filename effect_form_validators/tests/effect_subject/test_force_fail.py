from django.test import TestCase


class TestForcedFail(TestCase):
    def test_deliberate_fail(self):
        self.fail("Deliberate failing test to validate GH actions badge behaviour")
