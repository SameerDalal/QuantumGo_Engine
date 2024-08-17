import unittest
from action_space import make_action_map

action_map_5x5 = {
    0: [1, 1], 1: [1, 2], 2: [1, 3], 3: [1, 4], 4: [1, 5],
    5: [2, 1], 6: [2, 2], 7: [2, 3], 8: [2, 4], 9: [2, 5],
    10: [3, 1], 11: [3, 2], 12: [3, 3], 13: [3, 4], 14: [3, 5],
    15: [4, 1], 16: [4, 2], 17: [4, 3], 18: [4, 4], 19: [4, 5],
    20: [5, 1], 21: [5, 2], 22: [5, 3], 23: [5, 4], 24: [5, 5],
    25: 'pass', 26: 'resign'
}

class TestCalculations(unittest.TestCase):
    def test_make_action_map(self):
        self.assertEqual(make_action_map(5), action_map_5x5)