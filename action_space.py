def make_action_map(size: int):
    m = { (size * x + y): (x, y) for y in range(size) for x in range(size) }
    m[len(m)] = 'pass'
    m[len(m)] = 'resign'
    return m

action_map_5x5 = make_action_map(5)
reverse_action_map_5x5 = {v: k for k, v in action_map_5x5.items()}

action_map_9x9 = make_action_map(9)
reverse_action_map_9x9 = {v: k for k, v in action_map_9x9.items()}


action_map_19x19 = make_action_map(19)
reverse_action_map_19x19 = {v: k for k, v in action_map_19x19.items()}
