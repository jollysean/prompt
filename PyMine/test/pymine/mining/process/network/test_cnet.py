import unittest
from pymine.mining.process.network.cnet import CNet, CNode, InputBinding, OutputBinding
import logging
logging.basicConfig(level=logging.DEBUG, format="%(filename)s %(lineno)s %(levelname)s: %(message)s")


def _create_cnet():
    cnet = CNet()
    a, b, c, d, e = cnet.add_nodes('a', 'b', 'c', 'd', 'e')

    cnet.add_output_binding(a, {b, c})
    cnet.add_output_binding(a, {d})

    cnet.add_input_binding(b, {a})
    cnet.add_output_binding(b, {e})

    cnet.add_input_binding(c, {a})
    cnet.add_output_binding(c, {e})

    cnet.add_input_binding(d, {a})
    cnet.add_output_binding(d, {e})

    cnet.add_input_binding(e, {b, c})
    cnet.add_input_binding(e, {d})
    return cnet, a, b, c, d, e


class CNetTestCase(unittest.TestCase):

    def test_add_node(self):
        net = CNet()
        a = net.add_node('a')
        self.assertTrue(isinstance(a, CNode))
        self.assertTrue(len(a.input_bindings) == 0)
        self.assertTrue(len(a.output_bindings) == 0)

    def test_add_node_attrs(self):
        net = CNet()
        freq = 1
        attrs = {'test': True}
        a = net.add_node('a', frequency=freq, attrs=attrs)
        self.assertTrue(a.label == 'a')
        self.assertTrue(a.frequency == freq)
        self.assertTrue(a.attrs == attrs )

    def test_add_nodes(self):
        net = CNet()
        a, b = net.add_nodes('a', 'b')
        self.assertTrue(a.label == 'a')
        self.assertTrue(b.label == 'b')
        self.assertTrue(set(net.nodes) == {a, b})

    def test_add_bindings(self):
        net = CNet()
        a, b, c, d = net.add_nodes('a', 'b', 'c', 'd')
        binding_b_c = net.add_output_binding(a, {b, c})
        binding_b = net.add_output_binding(a, {b}, 1)
        binding_d_b = net.add_input_binding(d, {b})
        binding_d_c = net.add_input_binding(d, {c})

        self.assertTrue(a.output_bindings == [binding_b_c, binding_b])
        self.assertTrue(d.input_bindings == [binding_d_b, binding_d_c])
        self.assertTrue(set(net.bindings) == {binding_b, binding_b_c, binding_d_b, binding_d_c})

        self.assertTrue(isinstance(binding_b_c, OutputBinding))
        self.assertTrue(isinstance(binding_d_c, InputBinding))

        self.assertTrue(binding_b_c.node == a)
        self.assertTrue(binding_b_c.node_set == {b, c})
        self.assertTrue(binding_b.frequency == 1)

    def test_replay(self):
        cnet, a, b, c, d, e = _create_cnet()
        self.assertTrue(cnet.replay_sequence(['a', 'd', 'e'])[0])

    def test_replay_2(self):
        cnet = CNet()
        a, b, c, d = cnet.add_nodes('a', 'b', 'c', 'd')

        cnet.add_output_binding(a, {b, c})
        cnet.add_output_binding(a, {b})

        cnet.add_input_binding(b, {a})
        cnet.add_output_binding(b, {d})

        cnet.add_input_binding(c, {a})
        cnet.add_output_binding(c, {d})

        cnet.add_input_binding(d, {b})
        cnet.add_input_binding(d, {b, c})

        replay = cnet.replay_sequence(['a', 'b', 'd'])
        print replay
        self.assertTrue(replay[0])

    def test_replay_concurrency(self):
        cnet, a, b, c, d, e = _create_cnet()
        self.assertTrue(cnet.replay_sequence(['a', 'b', 'c',  'e'])[0])
        self.assertTrue(cnet.replay_sequence(['a', 'c', 'b',  'e'])[0])

    def test_replay_failing(self):
        cnet, a, b, c, d, e = _create_cnet()
        replay_result = cnet.replay_sequence(['a', 'd', 'd'])
        self.assertFalse(replay_result[0])
        self.assertEqual(set(replay_result[1]), {e})

    def test_replay_failing_unknown_events(self):
        cnet, a, b, c, d, e = _create_cnet()
        replay_result = cnet.replay_sequence(['a', 'd', 'y', 'e'])
        self.assertFalse(replay_result[0])
        self.assertEqual(len(replay_result[1]), 0)
        self.assertEqual(replay_result[2], ['y'])


