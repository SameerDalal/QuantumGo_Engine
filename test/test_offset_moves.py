import unittest
from offset_moves import get_offset_19x19
from action_space import action_map_19x19

class TestOffsetMoves(unittest.TestCase):
    def test_make_action_map(self):
        for action in action_map_19x19.values():
            if type(action) is str:
                break
            offset = get_offset_19x19(action)
            self.assertIsNotNone(offset[0], f"action={action}")
            self.assertIsNotNone(offset[1], f"action={action}")