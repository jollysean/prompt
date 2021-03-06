from prompt.mining.process.discovery import Miner as Miner
from prompt.mining.process.network.dependency import DependencyGraph as DependencyGraph
from prompt.mining.process.network.cnet import CNet as CNet
from prompt.mining.process.conformance import replay_case

from prompt.mining.process.eventlog.factory import CsvLogFactory as CsvLogFactory
from prompt.mining.process.eventlog.factory import ProcessInfo
import logging
logger = logging.getLogger('heuristic')


class HeuristicMiner(Miner):

    def calculate_arcs_dependency(self, net):
        for arc in net.arcs:
            a = float(arc.frequency)
            if arc.start_node != arc.end_node:
                logger.debug('arc.start_node != arc.end_node')
                reversed_arc = arc.end_node.label+"->"+arc.start_node.label
                r_arc = net.get_arc_by_label(reversed_arc)
                logger.debug('arc %s', arc)
                logger.debug('r_arc %s', r_arc)
                if r_arc:
                    logger.debug('r_arc.frequency %s', r_arc.frequency)
                    b = float(r_arc.frequency)
                    logger.debug('a=%s, b=%s', a, b)
                    arc.dependency = abs((a-b)/(a+b+1.0))
                    logger.debug('arc.dependency %s', arc.dependency)
                else:
                    arc.dependency = abs(a/(a+1.0))
                    logger.debug('else... arc.dependency %s', arc.dependency)
            else:
                logger.debug('arc.start_node == arc.end_node')
                dep = abs(a/(a+1.0))
                arc.dependency = dep
            logger.debug('arc %s freq %s', arc, arc.frequency)

    def prune_by_frequency(self, net, threshold):
        arcs_to_prune = []
        for arc in net.arcs:
            if arc.frequency < threshold:
                arcs_to_prune.append(arc)
        self._prune(net, arcs_to_prune)

    def prune_by_dependency(self, net, threshold):
        logger.debug('***********prune_by_dependency')
        arcs_to_prune = []
        for arc in net.arcs:
            if arc.dependency < threshold:
                arcs_to_prune.append(arc)
        logger.debug('prune_by_dependency %s', arcs_to_prune)
        self._prune(net, arcs_to_prune)

    def _prune(self, net, arcs):
        try:
            for a in list(arcs):
                #del net.arcs[a]
                net.remove_arc(a)
        except Exception as e:
            logger.exception(e)  # FIXME

    def mine_dependency_graph(self, process_log, frequency_threshold=None, dependency_threshold=None):

        net = DependencyGraph()
        # for each activity create a graph node
        process = process_log.process
        for activity in process.activities:
            net.add_node(label=activity.name)

        graph_start_node = net.get_node_by_label(process.cases[0].events[0].activity_instance.activity.name)
        graph_end_node = net.get_node_by_label(process.cases[0].events[-1].activity_instance.activity.name)
        for case in process.cases:
            # Insert some code here to check if start and end nodes are changing.
            # If true, an extra fake initial/final node should be added
            for e_index in xrange(0, len(case.events)-1):
                start_event = case.events[e_index]
                start_activity_instance = start_event.activity_instance
                start_activity = start_activity_instance.activity
                start_node_name = start_activity.name

                end_event = case.events[e_index+1]
                end_activity_instance = end_event.activity_instance
                end_activity = end_activity_instance.activity
                end_node_name = end_activity.name

                arc_name = start_node_name+"->"+end_node_name
                arc = net.get_arc_by_label(arc_name)
                if arc:
                    arc.frequency += 1
                else:
                    start_node = net.get_node_by_label(start_node_name)
                    end_node = net.get_node_by_label(end_node_name)
                    net.add_arc(start_node, end_node, arc_name, 1)
        net.start_node = graph_start_node
        net.end_node = graph_end_node
        self.calculate_arcs_dependency(net)

        if frequency_threshold:
            self.prune_by_frequency(net, frequency_threshold)
        logger.debug('*** dependency_threshold %s', dependency_threshold)
        if dependency_threshold:
            self.prune_by_dependency(net, dependency_threshold)

        # final_nodes = net.get_final_nodes()
        # if len(final_nodes) > 1:
        #     fake_final = net.add_node('__final')
        #     for n in final_nodes:
        #         net.add_arc(n, fake_final, frequency=1000)
        #
        # initial_nodes = net.get_initial_nodes()
        # if len(initial_nodes) > 1:
        #     fake_initial = net.add_node('__initial')
        #     for n in initial_nodes:
        #         net.add_arc(fake_initial, n, frequency=1000)

        return net

    def mine_cnet(self, dep_net, process_log, window_size=None, frequency_thr=0):
        p_info = ProcessInfo(process_log.process)

        window_size = window_size or int(p_info.average_case_size)
        c_net = CNet()
        for activity in dep_net.nodes:
            c_net.add_node(label=activity.label)
        c_net.start_node = dep_net.start_node
        c_net.end_node = dep_net.end_node
        for connection in dep_net.arcs:
            c_net.add_arc(c_net.get_node_by_label(connection.start_node.label),
                          c_net.get_node_by_label(connection.end_node.label),
                          label=connection.label,
                          frequency=connection.frequency)
        self.calculate_possible_binds(c_net, p_info.process, window_size, frequency_thr)


        # checking c_net soundness

        bad_loop_binding = []
        for b in c_net.output_bindings:
            if b.node in b.node_set and len(b.node_set) > 1:
                bad_loop_binding.append(b)

        for b in bad_loop_binding:
            c_net.remove_node_from_binding(b.node, b)
            c_net.add_output_binding(b.node, {b.node})

        bad_loop_binding = []
        for b in c_net.input_bindings:
            if b.node in b.node_set and len(b.node_set) > 1:
                bad_loop_binding.append(b)

        for b in bad_loop_binding:
            c_net.remove_node_from_binding(b.node, b)
            c_net.add_input_binding(b.node, {b.node})

        bad_shared_binding = []
        for b in c_net.output_bindings:
            logger.debug('binding %s, check for soundness', b)
            if len(b.node_set) > 1:
                output_nodes_set = []
                for node in b.node_set:
                    output_nodes_set.append(node.output_nodes)
                logger.debug('output_nodes_set %s for binding %s', output_nodes_set, b)
                if not set.intersection(*output_nodes_set):  # nodes does not share output node
                    bad_shared_binding.append(b)

        for b in bad_shared_binding:
            logger.debug('removing binding %s, no shared output node', b)
            c_net.remove_binding(b)
            for node in b.node_set:
                logger.debug('creationg binding %s -> {%s}', b.node, node)
                c_net.add_output_binding(b.node, {node})
                if b.node not in node.input_nodes:
                    c_net.add_input_binding(node, {b.node})

        # obls_to_rm = set()
        # logger.debug('checking for pending obligations')
        # for idx, case in enumerate(p_info.process.cases):
        #     passed, obls, unexpected = replay_case(case, c_net)
        #     logger.debug('idx %s, case %s, obls %s', idx, [e.activity_name for e in case.events], obls)
        #     obls_to_rm |= set(obls)
        #
        # logger.debug('obls_to_rm %s', obls_to_rm)
        # for obl in obls_to_rm:
        #     try:
        #         logger.debug('removing obl %s', obl)
        #         c_net.remove_node_from_binding(obl.node, obl.source_binding)
        #     except Exception as ex:
        #         logger.exception('ex %s', ex)  # FIXME use a specialized exception in case of non existing binding

        return c_net

    def calculate_possible_binds(self, c_net, process, window_size, frequency_thr):
        try:
            # for each case in the process log check the activity position
            for node in c_net.nodes:
                input_binds = {}
                output_binds = {}
                for case in process.cases:
                    try:
                        candidate_input_bind = []
                        candidate_output_bind = []
                        # check for multiple instances of the node on the current trace
                        node_indexes = [i for i, x in enumerate(case.activity_list) if x == node.label]
                        for node_index in node_indexes:
                            counter = 0
                            for event in case.events:
                                try:
                                    candidate_node = c_net.get_node_by_label(event.name)
                                    if counter <= node_index:
                                        #this is supposed to be before the node
                                        if not (counter == node_index) and \
                                                (candidate_node in node.input_nodes) and \
                                                ((node_index-counter) < window_size) and \
                                                (counter not in candidate_input_bind):
                                            candidate_input_bind.append(counter)
                                    else:
                                        #this is supposed to be after the node
                                        if (candidate_node in node.output_nodes) and \
                                                ((counter-node_index) < window_size) and \
                                                (counter not in candidate_output_bind):
                                            candidate_output_bind.append(counter)
                                    counter += 1
                                except Exception, e:
                                    print("Cannot compute bindins: "+str(e.message))
                        for i in xrange(len(candidate_input_bind)):
                            candidate_input_bind[i] = c_net.get_node_by_label(case.events[candidate_input_bind[i]].name)
                        for i in xrange(len(candidate_output_bind)):
                            candidate_output_bind[i] = c_net.get_node_by_label(case.events[candidate_output_bind[i]].name)

                        # Before inserting the candidate input bind, check if it contains the initial node
                        initial_node = c_net.start_node
                        for i in list(candidate_input_bind):
                            if initial_node.label == i.label:
                                candidate_input_bind.remove(i)
                                frozen_initial_node = frozenset({i})
                                if frozen_initial_node in input_binds:
                                    input_binds[frozen_initial_node] += 1
                                elif len(frozen_initial_node) > 0:
                                    input_binds[frozen_initial_node] = 1

                        frozen_candidate_input_bind = frozenset(candidate_input_bind)
                        if frozen_candidate_input_bind in input_binds:
                            input_binds[frozen_candidate_input_bind] += 1
                        elif len(frozen_candidate_input_bind) > 0:
                            input_binds[frozen_candidate_input_bind] = 1

                        # Before inserting the candidate output bind, check if it contains the final node
                        final_node = c_net.end_node
                        for i in list(candidate_output_bind):
                            if final_node.label == i.label:
                                candidate_output_bind.remove(i)
                                frozen_final_node = frozenset({i})
                                if frozen_final_node in output_binds:
                                    output_binds[frozen_final_node] += 1
                                elif len(frozen_final_node) > 0:
                                    output_binds[frozen_final_node] = 1

                        frozen_candidate_output_bind = frozenset(candidate_output_bind)
                        if frozen_candidate_output_bind in output_binds:
                            output_binds[frozen_candidate_output_bind] += 1
                        elif len(frozen_candidate_output_bind) > 0:
                            output_binds[frozen_candidate_output_bind] = 1
                    except ValueError, ve:
                        print("Value error: "+str(ve))
                for binds in input_binds:
                    if input_binds[binds] >= frequency_thr:
                        c_net.add_input_binding(node, set(binds), frequency=input_binds[binds])
                for binds in output_binds:
                    if output_binds[binds] >= frequency_thr:
                        c_net.add_output_binding(node, set(binds), frequency=output_binds[binds])

        except Exception, e:
            print("Error: "+str(e))

    def return_allowed_output_binds(self, binds_set):
        # Check which bind is allowed. TBD
        for bind in binds_set:
            pass
        return binds_set

    def return_allowed_input_binds(self, binds_set):
        # Check which bind is allowed. TBD
        for bind in binds_set:
            pass
        return binds_set

    def mine(self, process_log, arc_frequency_thr=0, dependency_thr=0.0, binding_frequency_thr=0, window_size=None):
        logger.debug('mine dependency_threshold %s', dependency_thr)
        dgraph = self.mine_dependency_graph(process_log, arc_frequency_thr, dependency_thr)
        cnet = self.mine_cnet(dgraph, process_log, window_size, binding_frequency_thr)
        return cnet

    def mine_from_csv_file(self, filename, frequency_threshold=0, dependency_threshold=0.0):
        log_file = CsvLogFactory(input_filename=filename)
        log = log_file.create_log()
        return self.mine(log, arc_frequency_thr=frequency_threshold, dependency_thr=dependency_threshold)