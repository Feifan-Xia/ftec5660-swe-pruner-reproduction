import unittest
from observation_store import ObservationStore


class RecoveryTests(unittest.TestCase):
    def test_exact_recovery_and_overlap(self):
        store = ObservationStore()
        text = 'alpha\r\nβeta\nlast'
        key = store.put(text)
        self.assertEqual(store.expand(key, 1, 3), text)
        self.assertEqual(store.expand(key, 2, 3), 'βeta\nlast')
        self.assertEqual(store.reads[-1]['repeated_lines'], 2)

    def test_invalid_reads_are_not_counted(self):
        store = ObservationStore(max_lines_per_read=1)
        key = store.put('a\nb')
        for args in [(key, 0, 1), (key, 1, 3), (key, 1, 2), ('missing', 1, 1)]:
            with self.assertRaises(ValueError):
                store.expand(*args)
        self.assertEqual(store.reads, [])


if __name__ == '__main__':
    unittest.main()
