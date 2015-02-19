import unittest
from pymine.mining.process.network import Network, Node, Arc


class NetworkTestCase(unittest.TestCase):

    def test_add_node(self):
        net = Network()
        a = net.add_node('a')

        self.assertTrue(isinstance(a, Node))
        self.assertTrue(a.label == 'a')
        self.assertTrue(net.nodes == [a])
        self.assertTrue(net.get_node_by_label('a') == a)

    def test_add_node_attrs(self):
        net = Network()
        freq = 1
        attrs = {'test': True}
        a = net.add_node('a', frequency=freq, attrs=attrs)

        print a.frequency
        self.assertTrue(isinstance(a, Node))
        self.assertTrue(a.label == 'a')
        self.assertTrue(a.frequency == freq)
        self.assertTrue(a.attrs == attrs )

        self.assertTrue(net.nodes == [a])
        self.assertTrue(net.get_node_by_label('a') == a)

    def test_add_nodes(self):
        net = Network()
        a, b = net.add_nodes('a', 'b')
        self.assertTrue(a.label == 'a')
        self.assertTrue(b.label == 'b')
        self.assertTrue(set(net.nodes) == {a, b})

    def test_add_arc(self):
        net = Network()
        a, b = net.add_nodes('a', 'b')
        arc = net.add_arc(a, b, 'arc')

        self.assertTrue(net.arcs == [arc])
        self.assertTrue(arc.label == 'arc')

        self.assertTrue(len(a.input_arcs) == 0)
        self.assertTrue(set(a.output_arcs) == {arc})

        self.assertTrue(len(b.output_arcs) == 0)
        self.assertTrue(set(b.input_arcs) == {arc})

        self.assertTrue(arc.input_node == b)
        self.assertTrue(arc.output_node == a)

        self.assertTrue(net.get_initial_nodes() == [a])
        self.assertTrue(net.get_final_nodes() == [b])
