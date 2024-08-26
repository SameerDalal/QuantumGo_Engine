import unittest
from action_space import make_action_map

action_map_3x3 = {
    0: (0, 0), 1: (0, 1), 2: (0, 2),
    3: (1, 0), 4: (1, 1), 5: (1, 2),
    6: (2, 0), 7: (2, 1), 8: (2, 2),
    9: 'pass', 10: 'resign'
}

class TestCalculations(unittest.TestCase):
    def test_make_action_map(self):
        self.assertEqual(make_action_map(3), action_map_3x3)