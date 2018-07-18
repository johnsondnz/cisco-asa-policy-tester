from logzero import logger
from .search import RecursiveSearch
from .resolve import Lookup, Resolve
from classes.structuredata import ASAPolicyTest
import re
import sys
import os


class TestControl(object):

    '''
    Class to construct and execute tests
    '''

    def __init__(self, script_dir, context, hostfile_status=False, hostfile_list=None):
        '''
        Initiate the class, allow any method to call the relevant source context data.
        '''

        self.context = context
        # logger.debug('Context data loaded')

        # initiate the test list for later execution.
        # all tests are stored against this list.
        self.testset = []

        # initaite the test results list
        # appended later to the jinja2_results dictionary
        self.test_results = []

        # initiate the storage dictionary
        # jinja2 expects a dictionary or anything
        self.jinja2_results = {}

        # setup the top level interface dictionaries
        # add this to the jinja2_results dictionary
        for interface, test_item in self.context.items():
            self.jinja2_results[interface] = {}
            # logger.debug('Dictionary for "{}" created.'.format(interface))

        # grab the hostfile information
        self.hostfile_status = hostfile_status
        self.hostfile_list = hostfile_list

        self.script_dir = script_dir

    def _host_lookup(self, test_data):
        '''
        Resolves names hosts to IP Address and/or validates provided strings are IP Addresses.
        Return dictionary of dictionaries
        '''

        if isinstance(test_data['source_ip'], list) and isinstance(test_data['destination_ip'], str):

            # logger.debug('List detect in destination_ip')

            # setup the dict and list
            ip_information = {}

            # record the source_ip
            destination_ip = Lookup(
                test_data['destination_ip'], self.hostfile_status, self.hostfile_list)
            ip_information['destination'] = destination_ip.get_ip()

            # setup list
            ip_information['sources'] = []

            for host in test_data['source_ip']:

                # store the destination_ip
                source_ip = Lookup(
                    host, self.hostfile_status, self.hostfile_list)
                ip_information['sources'].append(source_ip.get_ip())

        if isinstance(test_data['destination_ip'], list) and isinstance(test_data['source_ip'], str):

            # logger.debug('List detect in destination_ip')

            # setup the dict and list
            ip_information = {}

            # record the source_ip
            source_ip = Lookup(
                test_data['source_ip'], self.hostfile_status, self.hostfile_list)
            ip_information['source'] = source_ip.get_ip()

            # setup list
            ip_information['destinations'] = []

            for host in test_data['destination_ip']:

                # store the destination_ip
                destination_ip = Lookup(
                    host, self.hostfile_status, self.hostfile_list)
                ip_information['destinations'].append(destination_ip.get_ip())

        if isinstance(test_data['source_ip'], list) and isinstance(test_data['destination_ip'], list):

            # logger.debug('List detect in destination_ip')

            # setup the dict and list
            ip_information = {}

            # setup list
            ip_information['sources'] = []

            for host in test_data['source_ip']:

                # store the destination_ip
                source_ip = Lookup(
                    host, self.hostfile_status, self.hostfile_list)
                ip_information['sources'].append(source_ip.get_ip())

            # setup list
            ip_information['destinations'] = []

            for host in test_data['destination_ip']:

                # store the destination_ip
                destination_ip = Lookup(
                    host, self.hostfile_status, self.hostfile_list)
                ip_information['destinations'].append(destination_ip.get_ip())

        # it's not a list so move on to standard processing
        if isinstance(test_data['source_ip'], str) and isinstance(test_data['destination_ip'], str):

            source_ip = Lookup(
                test_data['source_ip'], self.hostfile_status, self.hostfile_list)
            destination_ip = Lookup(
                test_data['destination_ip'], self.hostfile_status, self.hostfile_list)

            ip_information = {
                'source': source_ip.get_ip(),
                'destination': destination_ip.get_ip()
            }

        return ip_information

    def _port_information(self, test_data):
        '''
        Takes test data and returns either a deictionary of port strings or a dictionary of list of ports for command construction to use.
        Current stores all sources and destinations.
        '''

        # setup the dict and list
        port_information = {}

        if isinstance(test_data['source_port'], list):

            # logger.debug('List detect in source_port')

            # setup the ports list
            port_information['sources'] = []

            for port in test_data['source_port']:

                # store the source_ports
                # validate that the ports lies within the range 0-65535
                if port <= 65535 and port >= 0:
                    port_information['sources'].append(
                        {'valid': True, 'port': port})
                else:
                    port_information['sources'].append(
                        {'valid': False, 'port': port})

        if isinstance(test_data['destination_port'], list):

            # logger.debug('List detect in destination_port')

            # setup the ports list
            port_information['destinations'] = []

            for port in test_data['destination_port']:

                # store the destination_ports
                # validate that the ports lies within the range 0-65535
                if port <= 65535 and port >= 0:
                    port_information['destinations'].append(
                        {'valid': True, 'port': port})
                else:
                    port_information['destinations'].append(
                        {'valid': False, 'port': port})

        # now check for integer/string fields
        if isinstance(test_data['source_port'], str) or isinstance(test_data['source_port'], int):

            # logger.debug('String or integer detect in source_port')

            # validate that the ports lies within the range 0-65535
            if test_data['source_port'] <= 65535 and test_data['source_port'] >= 0:
                port_information['source'] = {
                    'valid': True, 'port': test_data['source_port']}
            else:
                port_information['source'] = {
                    'valid': False, 'port': test_data['source_port']}

        if isinstance(test_data['destination_port'], str) or isinstance(test_data['destination_port'], int):

            # logger.debug('String or integer detect in destination_port')

            # validate that the ports lies within the range 0-65535
            if test_data['destination_port'] <= 65535 and test_data['destination_port'] >= 0:
                port_information['destination'] = {
                    'valid': True, 'port': test_data['destination_port']}
            else:
                port_information['destination'] = {
                    'valid': False, 'port': test_data['destination_port']}

        return port_information

    def _append_testlet(self, **kwargs):
        '''
        Takes a single testlet and appends it to the testset
        '''

        # logger.debug('-------- RECEIVED DATA -----------')
        # for k, v, in kwargs.items():
        #     logger.debug('{}: {}'.format(k,v))

        if re.match(r'(udp|tcp)', str(kwargs.get('protocol').lower())):

            # logger.debug('Processing {} data'.format(kwargs.get('protocol').lower()))

            command = 'packet-tracer input {} {} {} {} {} {} detail'.format(
                kwargs.get('interface'),
                kwargs.get('protocol'),
                kwargs.get('source_ip'),
                kwargs.get('source_port'),
                kwargs.get('destination_ip'),
                kwargs.get('destination_port')
            )

        elif 'icmp' in str(kwargs.get('protocol').lower()):

            # logger.debug('Processing {} data'.format(kwargs.get('protocol').lower()))

            command = 'packet-tracer input {} {} {} {} {} {} detail'.format(
                kwargs.get('interface'),
                kwargs.get('protocol'),
                kwargs.get('source_ip'),
                kwargs.get('icmp_type'),
                kwargs.get('icmp_code'),
                kwargs.get('destination_ip')
            )

        elif 'esp' in str(kwargs.get('protocol').lower()):
            command = 'packet-tracer input {} raw {} 50 {} detail'.format(
                kwargs.get('interface'),
                kwargs.get('source_ip'),
                kwargs.get('destination_ip')
            )

        # logger.debug('-------- APPENDED DATA -----------')
        # logger.debug({
        #     'interface': kwargs.get('interface'),
        #     'protocol': kwargs.get('protocol'),
        #     'source_ip': kwargs.get('source_ip'),
        #     'source_port': kwargs.get('source_port') if kwargs.get('source_port') is not None else '',
        #     'icmp_type': kwargs.get('icmp_type') if kwargs.get('icmp_type') is not None else '',
        #     'icmp_code': kwargs.get('icmp_code') if kwargs.get('icmp_code') is not None else '',
        #     'destination_ip': kwargs.get('destination_ip'),
        #     'destination_port': kwargs.get('destination_port') if kwargs.get('destination_port') is not None else '',
        #     'expected_result': kwargs.get('action'),
        #     'execute': kwargs.get('execute'),
        #     'command': command
        # })

        self.testset.append({
            'interface': kwargs.get('interface'),
            'index': kwargs.get('index'),
            'protocol': kwargs.get('protocol'),
            'source_ip': kwargs.get('source_ip'),
            'source_port': kwargs.get('source_port') if kwargs.get('source_port') is not None else '',
            'icmp_type': kwargs.get('icmp_type') if kwargs.get('icmp_type') is not None else '',
            'icmp_code': kwargs.get('icmp_code') if kwargs.get('icmp_code') is not None else '',
            'destination_ip': kwargs.get('destination_ip'),
            'destination_port': kwargs.get('destination_port') if kwargs.get('destination_port') is not None else '',
            'expected_result': kwargs.get('expected_result'),
            'execute': kwargs.get('execute'),
            'yaml_row': kwargs.get('yaml_row'),
            'command': command
        })

    def _construct_testlet(self, index, interface, ip_information, port_information, test_data, yaml_row):
        '''
        Builds the testset and returns it
        pushes the testlet into _append_testlet
        '''

        # setup the logic variables
        multiple_src_ips = True if RecursiveSearch(
            ip_information, 'sources') else False
        multiple_dest_ips = True if RecursiveSearch(
            ip_information, 'destinations') else False
        multiple_dest_ports = True if RecursiveSearch(
            port_information, 'destinations') else False

        # logger.debug('Multiples: {} {} {}'.format(multiple_src_ips,multiple_dest_ips,multiple_dest_ports))

        # logger.debug('-------- TEST DATA -----------')
        # for k,v in test_data.items():
        #     logger.debug('{}: {}'.format(k,v))

        # ------------------------------------------------------------------------------------------------------------------------- #
        # 0 0 0
        if multiple_src_ips == False and multiple_dest_ips == False and multiple_dest_ports == False:

            # if the source and destination IP are valid flag testlet for execution
            execute = True if ip_information['source']['result'] != False and ip_information[
                'destination']['result'] != False else False

            # Setup ICMP Type and Code

            testlet = {
                'index': index,
                'interface': interface,
                'protocol': test_data['protocol'],
                'source_ip': ip_information['source']['ip_address'],
                'icmp_type': test_data['icmp_type'] if isinstance(test_data['icmp_type'], int) else '',
                'icmp_code': test_data['icmp_code'] if isinstance(test_data['icmp_code'], int) else '',
                'source_port': test_data['source_port'] if test_data['source_port'] else '',
                'destination_ip': ip_information['destination']['ip_address'] if ip_information['destination']['ip_address'] else '',
                'destination_port': test_data['destination_port'] if test_data['destination_port'] else '',
                'expected_result': test_data['expected_result'],
                'yaml_row': yaml_row,
                'execute': execute
            }
            self._append_testlet(**testlet)

        # ------------------------------------------------------------------------------------------------------------------------- #
        # 0 0 1
        if multiple_src_ips == False and multiple_dest_ips == False and multiple_dest_ports == True:

            # ensure the destinations key is a list
            if isinstance(port_information['destinations'], list):

                for dest_port in port_information['destinations']:

                    # if the source and destination IP are valid flag testlet for executution
                    execute = True if ip_information['source']['result'] != False and ip_information[
                        'destination']['result'] != False else False

                    testlet = {
                        'index': index,
                        'interface': interface,
                        'protocol': test_data['protocol'],
                        'source_ip': ip_information['source']['ip_address'],
                        'icmp_type': test_data['icmp_type'] if isinstance(test_data['icmp_type'], int) else '',
                        'icmp_code': test_data['icmp_code'] if isinstance(test_data['icmp_code'], int) else '',
                        'source_port': test_data['source_port'] if test_data['source_port'] else '',
                        'destination_ip': ip_information['destination']['ip_address'] if ip_information['destination']['ip_address'] else '',
                        'destination_port': dest_port['port'] if dest_port['port'] else '',
                        'expected_result': test_data['expected_result'],
                        'yaml_row': yaml_row,
                        'execute': execute
                    }
                    self._append_testlet(**testlet)

        # ------------------------------------------------------------------------------------------------------------------------- #
        # 0 1 0
        if multiple_src_ips == False and multiple_dest_ips == True and multiple_dest_ports == False:

            # ensure the destinations key is a list
            if isinstance(ip_information['destinations'], list):

                for dest_ip in ip_information['destinations']:

                    # if the source and destination IP are valid flag testlet for executution
                    execute = True if ip_information['source']['result'] != False and dest_ip['result'] != False else False

                    testlet = {
                        'index': index,
                        'interface': interface,
                        'protocol': test_data['protocol'],
                        'source_ip': ip_information['source']['ip_address'],
                        'icmp_type': test_data['icmp_type'] if isinstance(test_data['icmp_type'], int) else '',
                        'icmp_code': test_data['icmp_code'] if isinstance(test_data['icmp_code'], int) else '',
                        'source_port': test_data['source_port'] if test_data['source_port'] else '',
                        'destination_ip': dest_ip['ip_address'] if dest_ip['ip_address'] else '',
                        'destination_port': test_data['destination_port'] if test_data['destination_port'] else '',
                        'expected_result': test_data['expected_result'],
                        'yaml_row': yaml_row,
                        'execute': execute
                    }

                    self._append_testlet(**testlet)

        # ------------------------------------------------------------------------------------------------------------------------- #
        # 0 1 1
        if multiple_src_ips == False and multiple_dest_ips == True and multiple_dest_ports == True:

            if isinstance(ip_information['destinations'], list):

                for dest_ip in ip_information['destinations']:

                    # if the source and destination IP are valid flag testlet for executution
                    execute = True if ip_information['source']['result'] != False and dest_ip['result'] != False else False

                    # ensure the destinations key is a list
                    if isinstance(port_information['destinations'], list):

                        for dest_port in port_information['destinations']:

                            testlet = {
                                'index': index,
                                'interface': interface,
                                'protocol': test_data['protocol'],
                                'source_ip': ip_information['source']['ip_address'],
                                'icmp_type': test_data['icmp_type'] if isinstance(test_data['icmp_type'], int) else '',
                                'icmp_code': test_data['icmp_code'] if isinstance(test_data['icmp_code'], int) else '',
                                'source_port': test_data['source_port'] if test_data['source_port'] else '',
                                'destination_ip': dest_ip['ip_address'] if dest_ip['ip_address'] else '',
                                'destination_port': dest_port['port'] if dest_port['port'] else '',
                                'expected_result': test_data['expected_result'],
                                'yaml_row': yaml_row,
                                'execute': execute
                            }
                            self._append_testlet(**testlet)
        # ------------------------------------------------------------------------------------------------------------------------- #
        # 1 0 0
        if multiple_src_ips == True and multiple_dest_ips == False and multiple_dest_ports == False:

            if isinstance(ip_information['sources'], list):

                for src_ip in ip_information['sources']:

                    # if the source and destination IP are valid flag testlet for executution
                    execute = True if ip_information['destination'][
                        'result'] != False and src_ip['result'] != False else False

                    testlet = {
                        'index': index,
                        'interface': interface,
                        'protocol': test_data['protocol'],
                        'source_ip': src_ip['ip_address'],
                        'icmp_type': test_data['icmp_type'] if isinstance(test_data['icmp_type'], int) else '',
                        'icmp_code': test_data['icmp_code'] if isinstance(test_data['icmp_code'], int) else '',
                        'source_port': test_data['source_port'] if test_data['source_port'] else '',
                        'destination_ip': ip_information['destination']['ip_address'] if ip_information['destination']['ip_address'] else '',
                        'destination_port': test_data['destination_port'] if test_data['destination_port'] else '',
                        'expected_result': test_data['expected_result'],
                        'yaml_row': yaml_row,
                        'execute': execute
                    }

                    self._append_testlet(**testlet)
        # ------------------------------------------------------------------------------------------------------------------------- #
        # 1 0 1
        if multiple_src_ips == True and multiple_dest_ips == False and multiple_dest_ports == True:

            if isinstance(ip_information['sources'], list):

                for src_ip in ip_information['sources']:

                    # if the source and destination IP are valid flag testlet for executution
                    execute = True if ip_information['destination'][
                        'result'] != False and src_ip['result'] != False else False

                    # ensure the destinations key is a list
                    if isinstance(port_information['destinations'], list):

                        for dest_port in port_information['destinations']:

                            testlet = {
                                'index': index,
                                'interface': interface,
                                'protocol': test_data['protocol'],
                                'source_ip': src_ip['ip_address'],
                                'icmp_type': test_data['icmp_type'] if isinstance(test_data['icmp_type'], int) else '',
                                'icmp_code': test_data['icmp_code'] if isinstance(test_data['icmp_code'], int) else '',
                                'source_port': test_data['source_port'] if test_data['source_port'] else '',
                                'destination_ip': ip_information['destination']['ip_address'] if ip_information['destination']['ip_address'] else '',
                                'destination_port': dest_port['port'] if dest_port['port'] else '',
                                'expected_result': test_data['expected_result'],
                                'yaml_row': yaml_row,
                                'execute': execute
                            }
                            self._append_testlet(**testlet)
        # ------------------------------------------------------------------------------------------------------------------------- #
        # 1 1 0
        if multiple_src_ips == True and multiple_dest_ips == True and multiple_dest_ports == False:

            if isinstance(ip_information['sources'], list) and isinstance(ip_information['destinations'], list):

                for src_ip in ip_information['sources']:

                    for dest_ip in ip_information['destinations']:

                        # if the source and destination IP are valid flag testlet for executution
                        execute = True if src_ip['result'] != False and dest_ip['result'] != False else False

                        testlet = {
                            'index': index,
                            'interface': interface,
                            'protocol': test_data['protocol'],
                            'source_ip': src_ip['ip_address'],
                            'icmp_type': test_data['icmp_type'] if isinstance(test_data['icmp_type'], int) else '',
                            'icmp_code': test_data['icmp_code'] if isinstance(test_data['icmp_code'], int) else '',
                            'source_port': test_data['source_port'] if test_data['source_port'] else '',
                            'destination_ip': dest_ip['ip_address'] if dest_ip['ip_address'] else '',
                            'destination_port': test_data['destination_port'] if test_data['destination_port'] else '',
                            'expected_result': test_data['expected_result'],
                            'yaml_row': yaml_row,
                            'execute': execute
                        }
                        self._append_testlet(**testlet)
        # ------------------------------------------------------------------------------------------------------------------------- #
        # 1 1 1
        if multiple_src_ips == True and multiple_dest_ips == True and multiple_dest_ports == True:

            if isinstance(ip_information['sources'], list) and isinstance(ip_information['destinations'], list):

                for src_ip in ip_information['sources']:

                    for dest_ip in ip_information['destinations']:

                        # if the source and destination IP are valid flag testlet for executution
                        execute = True if src_ip['result'] != False and dest_ip['result'] != False else False

                        # ensure the destinations key is a list
                        if isinstance(port_information['destinations'], list):

                            for dest_port in port_information['destinations']:

                                testlet = {
                                    'index': index,
                                    'interface': interface,
                                    'protocol': test_data['protocol'],
                                    'source_ip': src_ip['ip_address'],
                                    'icmp_type': test_data['icmp_type'] if isinstance(test_data['icmp_type'], int) else '',
                                    'icmp_code': test_data['icmp_code'] if isinstance(test_data['icmp_code'], int) else '',
                                    'source_port': test_data['source_port'] if test_data['source_port'] else '',
                                    'destination_ip': dest_ip['ip_address'] if dest_ip['ip_address'] else '',
                                    'destination_port': dest_port['port'] if dest_port['port'] else '',
                                    'expected_result': test_data['expected_result'],
                                    'yaml_row': yaml_row,
                                    'execute': execute
                                }
                                self._append_testlet(**testlet)
        # ------------------------------------------------------------------------------------------------------------------------- #

    def construct_testset(self):
        '''
        Takes the contaxt YAML data and constructs commandset with expected outcomes for each test.

        Accepts lists for:
          - Destination IP

        Returns the testset for use un exectute method.
        '''

        # iterate through the interface dictionary and actions list
        for interface, item in self.context.items():

            # iterate through the action list
            for index, test_data in enumerate(item):

                # logger.debug('Processing test item {}'.format(index))

                # will use this later for a HTML5/Bootstrap on-hover tooltip.
                # Sent to self.jinja2_results later
                # Use this to ensure presented data is the raw row from yaml
                # Not the processed information post name resolution etc.
                self.yaml_row = test_data

                # logger.debug('item {} data: {}'.format(index,self.yaml_row))

                ip_information = self._host_lookup(test_data)
                port_information = self._port_information(test_data)

                self._construct_testlet(index,
                                        interface, ip_information, port_information, test_data, self.yaml_row)

        return self.testset

    def execute(self, testset, connect):
        '''
        The main brains of the operation.
        Called after the contruct methods
        '''

        # first setup each dictionary for expected_results and interface test_stats
        for test_data in testset:
            self.jinja2_results[test_data['interface']]['should_{}'.format(
                test_data['expected_result'])] = []
            self.jinja2_results[test_data['interface']]['interface_stats'] = {}
            self.jinja2_results[test_data['interface']]['interface_stats']['total'] = 0
            self.jinja2_results[test_data['interface']]['interface_stats']['skip'] = 0
            self.jinja2_results[test_data['interface']]['interface_stats']['pass'] = 0
            self.jinja2_results[test_data['interface']]['interface_stats']['fail'] = 0

        # setup total play teststats dictionary
        self.jinja2_results['full_stats'] = {}
        self.jinja2_results['full_stats']['total'] = 0
        self.jinja2_results['full_stats']['skip'] = 0
        self.jinja2_results['full_stats']['pass'] = 0
        self.jinja2_results['full_stats']['fail'] = 0

        for index, test_data in enumerate(testset):

            # process only tasks flagged for execution (True)
            # items flagged as False could not have IP Addresses resolved
            if test_data['execute'] == True:

                self.jinja2_results['full_stats']['total'] += 1
                self.jinja2_results[test_data['interface']]['interface_stats']['total'] += 1

                logger.info('Excuting interface {}'.format(
                    test_data['interface']))
                logger.info('Command: {}'.format(test_data['command']))

                cli_output = connect.send_command(test_data['command'])
                ParseData = ASAPolicyTest(self.script_dir, cli_output)
                test_results = ParseData.TestResult()

                # log to terminal the overall ASA action
                logger.info('Expecting: {}'.format(
                    test_data['expected_result']))
                logger.info('ASA reports: {}'.format(
                    test_results['asa_action']))

                # if NAT is reported log to terminal
                if test_results['nat_rule'] is not None:
                    logger.info('NAT detected: {} to {}'.format(
                        test_results['nat_from'], test_results['nat_to']))
                    logger.info('NAT rule: "{}"'.format(
                        test_results['nat_rule']))

                # log to terminal the drop reason if it exists
                if test_results['drop_reason'] is not None:
                    logger.info('Drop reason: {}'.format(
                        test_results['drop_reason']))

                # log to terminal the test result
                if test_results['asa_action'] == test_data['expected_result']:
                    logger.info('Test passed!\n')
                    grade = '[PASS]'
                    self.jinja2_results['full_stats']['pass'] += 1
                    self.jinja2_results[test_data['interface']]['interface_stats']['pass'] += 1
            
                else:
                    logger.error('Test failed!\n')
                    grade = '[FAIL]'
                    self.jinja2_results['full_stats']['fail'] += 1
                    self.jinja2_results[test_data['interface']]['interface_stats']['fail'] += 1

                self.jinja2_results[test_data['interface']]['should_{}'.format(test_data['expected_result'])].append({
                    'command': test_data['command'],
                    'index': test_data['index'],
                    'interface': test_data['interface'],
                    'protocol': test_data['protocol'],
                    'source_ip': test_data['source_ip'],
                    'source_port': test_data['source_port'] if test_data['source_port'] is not None else '',
                    'icmp_type': test_data['icmp_type'] if isinstance(test_data['icmp_type'], int) else '',
                    'icmp_code': test_data['icmp_code'] if isinstance(test_data['icmp_code'], int) else '',
                    'output_interface': test_results['output_interface'],
                    'destination_ip': test_data['destination_ip'],
                    'destination_port': test_data['destination_port'] if test_data['destination_port'] is not None else '',
                    'expected_result': test_data['expected_result'],
                    'asa_action': test_results['asa_action'] if test_results['asa_action'] is not None else '',
                    'drop_reason': test_results['drop_reason'] if test_results['drop_reason'] is not None else '',
                    'nat_from': test_results['nat_from'] if test_results['nat_from'] is not None else '',
                    'nat_to': test_results['nat_to'] if test_results['nat_to'] is not None else '',
                    'nat_rule': test_results['nat_rule'] if test_results['nat_rule'] is not None else '',
                    'yaml_row': test_data['yaml_row'],
                    'grade': grade
                })
            else:
                self.jinja2_results['full_stats']['skip'] += 1
                self.jinja2_results[test_data['interface']]['interface_stats']['skip'] += 1
                self.jinja2_results[test_data['interface']]['should_{}'.format(test_data['expected_result'])].append({
                    'command': test_data['command'],
                    'index': test_data['index'],
                    'interface': test_data['interface'],
                    'protocol': test_data['protocol'],
                    'source_ip': test_data['source_ip'],
                    'source_port': test_data['source_port'] if test_data['source_port'] is not None else '',
                    'icmp_type': test_data['icmp_type'] if isinstance(test_data['icmp_type'], int) else '',
                    'icmp_code': test_data['icmp_code'] if isinstance(test_data['icmp_code'], int) else '',
                    'output_interface': test_results['output_interface'],
                    'destination_ip': test_data['destination_ip'],
                    'destination_port': test_data['destination_port'] if test_data['destination_port'] is not None else '',
                    'expected_result': test_data['expected_result'],
                    'asa_action': '',
                    'drop_reason': '',
                    'nat_from': '',
                    'nat_to': '',
                    'nat_rule': '',
                    'yaml_row': test_data['yaml_row'],
                    'grade': '[SKIP]'
                })
                logger.error('Skipping test record "{}" for interface "{}", unable to resolve address(es) from this testlet.\n'.format(
                    test_data['yaml_row'], test_data['interface']))

        # # append the loops test results to the jinja2 dictionary and return jinja2 dictionary to main.
        # self.jinja2_results[test_data['interface']]['should_{}'.format(
        #     test_data['expected_result'])] = self.test_results

        # Look for failed tests, call method to generate retry.yml if found
        if RecursiveSearch(self.jinja2_results, 'grade', 'FAIL'):
            # delete any retry file before starting
            self._delete_retry()

            logger.info('tests/retry.yml generated for failed items reruns')
            self._retry_tests()

        # return the results for report processing
        return self.jinja2_results

    def _delete_retry(self):
        import os

        try:
            os.unlink('{}/tests/retry.yml'.format(self.script_dir))
        except Exception:
            logger.info('tests/retry.yml missing, moving on')
            pass

    def _retry_tests(self):
        '''
        Parses self.jinja2_results and extracts failed tests.
        Generates tests/retry.yml
        '''

        import yaml

        # setup the retry dictionary
        testset = {}

        # setup the interface dictionarys keys
        for interface, result in self.jinja2_results.items():
            testset[interface] = []

        # open the file for appending
        with open('{}/tests/retry.yml'.format(self.script_dir), 'a') as outfile:

            # iterate through the test results
            for interface, result in self.jinja2_results.items():

                # omit processing full test suite test_stats
                if interface != 'full_stats':

                    for item, data in result.items():

                        # omit processing interface test_stats
                        if item != 'interface_stats':

                            for item in data:

                                    if item['grade'] == '[FAIL]' or item['grade'] == '[SKIP]':

                                        retry_dict = {
                                            'protocol': item['protocol'],
                                            'icmp_type': item['icmp_type'] if isinstance(item['icmp_type'], int) else None,
                                            'icmp_code': item['icmp_code'] if isinstance(item['icmp_type'], int) else None,
                                            'source_ip': item['source_ip'],
                                            'source_port': item['source_port'] if item['source_port'] else None,
                                            'destination_ip': item['destination_ip'],
                                            'destination_port': item['destination_port'] if item['destination_port'] else None,
                                            'expected_result': item['expected_result']
                                        }

                                        # logger.debug('apending {}'.format(retry_dict))

                                        testset[interface].append(retry_dict)

            yaml.dump(testset, outfile, default_flow_style=True)
            outfile.close()
