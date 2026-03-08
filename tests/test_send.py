import unittest


class TestSendScript(unittest.TestCase):
    @unittest.skip("Manual GUI integration test; requires desktop automation environment")
    def test_manual_send(self):
        self.fail("manual test placeholder")


if __name__ == "__main__":
    unittest.main()
