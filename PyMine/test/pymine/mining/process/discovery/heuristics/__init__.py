from pymine.mining.process.eventlog.factory import create_process_log_from_list, create_log_from_file
from pymine.mining.process.conformance import simple_fitness
import unittest
import os


def get_binding_set(binding):
    return {frozenset(bi.node_set) for bi in binding}


class BackendTests(object):
    def create_miner(self, log):
        raise NotImplementedError

    def __getattr__(self, item):
        return getattr(unittest.TestCase, item)

    def test_2_and_1_xor(self):
        log = create_process_log_from_list([
            ['a', 'b', 'c', 'e'],
            ['a', 'c', 'b', 'e'],
            ['a', 'd', 'e'],
        ])
        miner = self.create_miner(log)
        cnet = miner.mine()
        a, b, c, d, e = [cnet.get_node_by_label(n) for n in ['a', 'b', 'c', 'd', 'e']]
        self.assertEqual(cnet.get_initial_nodes(), [a])
        self.assertEqual(cnet.get_final_nodes(), [e])
        self.assertTrue(a.output_bindings, {frozenset({b, c}), frozenset({d})})
        self.assertTrue(e.input_bindings, {frozenset({b, c}), frozenset({d})})

    def test_triple_and(self):
        log = create_process_log_from_list([
        ['a', 'b', 'c', 'd', 'e'],
        ['a', 'b', 'd', 'c', 'e'],
        ['a', 'c', 'b', 'd', 'e'],
        ['a', 'c', 'd', 'b', 'e'],
        ['a', 'd', 'b', 'c', 'e'],
        ['a', 'd', 'c', 'b', 'e'],
        ])
        miner = self.create_miner(log)
        cnet = miner.mine()
        a, b, c, d, e = [cnet.get_node_by_label(n) for n in ['a', 'b', 'c', 'd', 'e']]
        self.assertEqual(cnet.get_initial_nodes(), [a])
        self.assertEqual(cnet.get_final_nodes(), [e])
        self.assertEqual({bi.node_set for bi in a.output_bindings}, {frozenset({b, c, d})})
        self.assertTrue({bi.node for bi in e.input_bindings}, {frozenset({b, c, d})})

    def test_3_and_couple(self):
        log = create_process_log_from_list([
            ['a', 'b', 'c', 'd'],
            ['a', 'c', 'b', 'd'],
            ['a', 'c', 'e', 'd'],
            ['a', 'e', 'c', 'd'],
            ['a', 'b', 'e', 'd'],
            ['a', 'e', 'b', 'd'],
        ])
        miner = self.create_miner(log)
        cnet = miner.mine(and_thr=0.2)
        a, b, c, d, e = [cnet.get_node_by_label(n) for n in ['a', 'b', 'c', 'd', 'e']]
        self.assertEqual(cnet.get_initial_nodes(), [a])
        self.assertEqual(cnet.get_final_nodes(), [d])
        self.assertEqual({frozenset(bi.node_set) for bi in a.output_bindings},
                         {frozenset({b, c}), frozenset({b, e}), frozenset({c, e})})
        self.assertEqual({frozenset(bi.node_set) for bi in d.input_bindings},
                         {frozenset({b, c}), frozenset({b, e}), frozenset({c, e})})

    def test_2_groups_and(self):
        log = create_process_log_from_list([
            ['a', 'b1', 'b2', 'd'],
            ['a', 'b2', 'b1', 'd'],
            ['a', 'tb1', 'tb2', 'd'],
            ['a', 'tb2', 'tb1', 'd'],
            ['a', 'b1', 'tb2', 'd'],
            ['a', 'tb2', 'b1', 'd'],
            ['a', 'tb1', 'b2', 'd'],
            ['a', 'b2', 'tb1', 'd'],
        ])
        miner = self.create_miner(log)
        cnet = miner.mine(and_thr=0.2)
        a, b1, b2, tb1, tb2,  d = [cnet.get_node_by_label(n) for n in ['a', 'b1', 'b2', 'tb1', 'tb2', 'd']]
        self.assertEqual(cnet.get_initial_nodes(), [a])
        self.assertEqual(cnet.get_final_nodes(), [d])
        self.assertEqual({frozenset(bi.node_set) for bi in a.output_bindings},
                        {frozenset({b1, b2}), frozenset({b1, tb2}), frozenset({b2, tb1}), frozenset({tb1, tb2})})
        self.assertEqual({frozenset(bi.node_set) for bi in d.input_bindings},
                        {frozenset({b1, b2}), frozenset({b1, tb2}), frozenset({b2, tb1}), frozenset({tb1, tb2})})

    def test_pg_4_dataset(self):
        dataset_path = os.path.join(os.path.dirname(__file__), '../../../../../../dataset/pg_4_label_final_node.csv')
        log = create_log_from_file(dataset_path)[0]
        miner = self.create_miner(log)
        cnet = miner.mine()
        a, b, c, d, e, f, g, h, z = [cnet.get_node_by_label(n) for n in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'z']]
        self.assertEqual(cnet.get_initial_nodes(), [a])
        self.assertEqual(cnet.get_final_nodes(), [z])

        self.assertEqual(get_binding_set(a.output_bindings), {frozenset({b, d}), frozenset({c, d})})

        self.assertEqual(get_binding_set(b.input_bindings), {frozenset({a}), frozenset({f})})
        self.assertEqual(get_binding_set(b.output_bindings), {frozenset({e})})

        self.assertEqual(get_binding_set(c.input_bindings), {frozenset({a}), frozenset({f})})
        self.assertEqual(get_binding_set(c.output_bindings), {frozenset({e})})

        self.assertEqual(get_binding_set(d.input_bindings), {frozenset({a}), frozenset({f})})
        self.assertEqual(get_binding_set(d.output_bindings), {frozenset({e})})

        self.assertEqual(get_binding_set(e.input_bindings), {frozenset({b, d}), frozenset({c, d})})
        self.assertEqual(get_binding_set(e.output_bindings), {frozenset({f}), frozenset({g}), frozenset({h})})

        self.assertEqual(get_binding_set(f.input_bindings), {frozenset({e})})
        self.assertEqual(get_binding_set(f.output_bindings), {frozenset({b, d}), frozenset({c, d})})

        self.assertEqual(get_binding_set(g.input_bindings), {frozenset({e})})
        self.assertEqual(get_binding_set(g.output_bindings), {frozenset({z})})

        self.assertEqual(get_binding_set(h.input_bindings), {frozenset({e})})
        self.assertEqual(get_binding_set(h.output_bindings), {frozenset({z})})

        self.assertEqual(get_binding_set(z.input_bindings), {frozenset({g}), frozenset({h})})

    def test_2_step_loop(self):
        log = create_process_log_from_list([
            ['a', 'b', 'c', 'd'],
            ['a', 'b', 'c', 'b', 'c', 'd'],
            ['a', 'b', 'c', 'b', 'c', 'b', 'c', 'd'],

        ])
        miner = self.create_miner(log)
        cnet = miner.mine(and_thr=0.2)
        a, b, c, d = [cnet.get_node_by_label(n) for n in ['a', 'b', 'c', 'd']]
        self.assertEqual(cnet.get_initial_nodes(), [a])
        self.assertEqual(cnet.get_final_nodes(), [d])

        self.assertEqual(get_binding_set(a.output_bindings), {frozenset({b})})

        self.assertEqual(get_binding_set(b.input_bindings), {frozenset({a}), frozenset({c})})
        self.assertEqual(get_binding_set(b.output_bindings), {frozenset({c})})

        self.assertEqual(get_binding_set(c.input_bindings), {frozenset({b})})
        self.assertEqual(get_binding_set(c.output_bindings), {frozenset({b}), frozenset({d})})

        self.assertEqual(get_binding_set(d.input_bindings), {frozenset({c})})

