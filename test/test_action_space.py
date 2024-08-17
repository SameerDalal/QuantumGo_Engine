import unittest
from action_space import make_action_map

action_map_3x3 = {
    0: (1, 1), 1: (1, 2), 2: (1, 3),
    3: (2, 1), 4: (2, 2), 5: (2, 3),
    6: (3, 1), 7: (3, 2), 8: (3, 3),
    9: 'pass', 10: 'resign'
}

class TestCalculations(unittest.TestCase):
    def test_make_action_map(self):
        self.assertEqual(make_action_map(3), action_map_3x3)