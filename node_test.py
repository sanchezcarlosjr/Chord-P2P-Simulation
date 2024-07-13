from node import ChordNode

def test_init():
    node_set = [1,4,9,11,14,18,20,21,28]
    ring = []
    for i in range(len(node_set)):
        ring.append(ChordNode(node_set[i], ring, i))
    heartbeats = [iter(node.heartbeat()) for node in ring]
    global_finger_table = [[28,4,4,9,9,18,1], [1,9,9,9,14,20,4], [4, 11, 11, 14, 18, 28, 9], [9,14,14,18,20,28,11], [11, 18,18,18,28,1, 14], [14, 20, 20, 28, 28, 4, 18],  [18, 21, 28, 28, 28, 4, 20], [20, 28, 28, 28, 1, 9, 21], [21, 1,1,1,4,14, 28]]
    for index, finger_table in enumerate(global_finger_table):
        assert next(heartbeats[index])[2] == finger_table
    ring[0].set(26, "Chrod Algorithm")
    assert ring[0].get(26) == "Chrod Algorithm"
    assert ring[0].find_node(26).nodeID == 28
    assert ring[0].find_node(29).nodeID == 1
    assert ring[1].find_node(1).nodeID == 1

