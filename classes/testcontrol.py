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
        logger.debug('Context data loaded')

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
            logger.debug('Dictionary for "{}" created.'.format(interface))

        # grab the hostfile information
        self.hostfile_status = hostfile_status
        self.hostfile_list = hostfile_list

        self.script_dir = script_dir

    def _host_lookup(self, test_data):
        '''
        Resolves names hosts to IP Address and/or validates provided strings are IP Addresses.
        Return dictionary of dictionaries
        '''

        if isinstance(test_data['destination_ip'], list):

            '''
            normalises ip_information and commands
            indexing will ensure the test and command line up in the pust to testset
            '''

            logger.debug('List detect in destination_ip')
            
            # setup the dict and list
            ip_information = {}

            # record the source_ip
            source_ip = Lookup(test_data['source_ip'], self.hostfile_status, self.hostfile_list)
            ip_information['source'] = source_ip.get_ip()

            # setup destinations list
            ip_information['destinations'] = []

            for host in test_data['destination_ip']:

                # store the destination_ip
                destination_ip = Lookup(host, self.hostfile_status, self.hostfile_list)
                ip_information['destinations'].append(destination_ip.get_ip())

        # it's not a list so move on to standard processing
        else:
            
            source_ip = Lookup(test_data['source_ip'], self.hostfile_status, self.hostfile_list)
            destination_ip = Lookup(test_data['destination_ip'], self.hostfile_status, self.hostfile_list)

            ip_information = {
                'source': source_ip.get_ip(),
                'destination': destination_ip.get_ip()
            }
        
        print(ip_information)
        return ip_information

    def _construct_command(self, interface, ip_information, test_data):
        '''
        Builds a single command for a testset
        Returns a dictionary the indicates if a list of commands follows or a single commands
        '''

        # Check for the destinations key which means a list will follow
        if RecursiveSearch(ip_information, 'destinations'):
            # ensure the destinations key is a list
            if isinstance(ip_information['destinations'], list):

                '''
                List detection
                '''

                command = []

                for dest_ip in ip_information['destinations']:

                    if re.match(r'(udp|tcp)', str(test_data['protocol'].lower())):

                        cmd = 'packet-tracer input {} {} {} {} {} {} detail'.format(
                            interface, test_data['protocol'], ip_information['source']['ip_address'], test_data['source_port'], dest_ip['ip_address'], test_data['destination_port'])
                        command.append(cmd)
                        logger.info('storing {}'.format(cmd))

                    elif 'icmp' in str(test_data['protocol'].lower()):

                        cmd = 'packet-tracer input {} {} {} {} {} {} detail'.format(
                            interface, test_data['protocol'], ip_information['source']['ip_address'], test_data['icmp_type'], test_data['icmp_code'], dest_ip['ip_address'])
                        command.append(cmd)
                        logger.info('storing {}'.format(cmd))

        else:

            if re.match(r'(udp|tcp)', str(test_data['protocol'].lower())):

                command = 'packet-tracer input {} {} {} {} {} {} detail'.format(
                    interface, test_data['protocol'], ip_information['source']['ip_address'], test_data['source_port'], ip_information['destination']['ip_address'], test_data['destination_port'])

            elif 'icmp' in str(test_data['protocol'].lower()):

                command = 'packet-tracer input {} {} {} {} {} {} detail'.format(
                    interface, test_data['protocol'], ip_information['source']['ip_address'], test_data['icmp_type'], test_data['icmp_code'], ip_information['destination']['ip_address'])

        if isinstance(command, list):
            return { 'list': True, 'commands': command }
        else:
            return { 'list': False, 'command': command }

    def _append_test_yes(self, **data):

        '''
        Appends a test that will be executed.
        '''

        pass

    
    def _append_test_no(self, **data):

        '''
        Appends a test that will be skipped.
        '''

        pass


    def construct_testset(self):
        '''
        Takes the contaxt YAML data and constructs commandset with expected outcomes for each test.

        Accepts lists for:
          - Destination IP

        Returns the testset for use un exectute method.
        '''

        # create the action items
        actions = ['allow', 'drop']

        for action in actions:

            # iterate through the interface dictionary and actions list
            for interface, item in self.context.items():

                # check that the interface dictionary contains the action item list
                if RecursiveSearch(item, action):

                    logger.info('Constructing "{}", "{}" tests'.format(
                        interface, action))

                    # iterate through the action list
                    for index, test_data in enumerate(item[action]):

                        logger.info('Processing {} protocol policy'.format(
                            test_data['protocol'].lower()))
                        
                        ip_information = self._host_lookup(test_data)

                        command = self._construct_command(
                            interface, ip_information, test_data)

                        '''
                        Append the test to the testset
                        [
                            {
                                yaml_row,   # in case of multiple checks per test
                                interface,
                                protocol,
                                source_ip,
                                source_port,
                                destination_ip,
                                destination_port,
                                expected_result
                            },

                            OR

                            {
                                yaml_row,   # in case of multiple checks per test
                                interface,
                                protocol,
                                source_ip,
                                icmp_type,
                                test_data
                                icmp_code,
                                destination_ip,
                                expected_result
                            }
                        ]
                        '''

                        if command['list'] == True:

                            for cmd_index, cmd in enumerate(command['commands']):

                                if ip_information['source']['result'] != False and ip_information['destinations'][cmd_index]['result'] != False:

                                    self.testset.append({
                                        'test_record': index,
                                        'interface': interface,
                                        'protocol': test_data['protocol'],
                                        'source_ip': ip_information['source']['ip_address'],
                                        'source_port': test_data['source_port'] if test_data['source_port'] is not None else '',
                                        'icmp_type': test_data['icmp_type'] if test_data['icmp_type'] is not None else '',
                                        'icmp_code': test_data['icmp_code'] if test_data['icmp_code'] is not None else '',
                                        'destination_ip': ip_information['destinations'][cmd_index],
                                        'destination_port': test_data['destination_port'] if test_data['destination_port'] is not None else '',
                                        'expected_result': action,
                                        'execute': True,
                                        'command': cmd,
                                        'action': action
                                    })
                                    logger.info('Test record "{}" for interface "{}" stored for execution\n'.format(
                                        index, interface))

                                else:
                                    self.testset.append({
                                        'test_record': index,
                                        'interface': interface,
                                        'protocol': test_data['protocol'],
                                        'source_ip': ip_information['source']['ip_address'],
                                        'source_port': test_data['source_port'] if test_data['source_port'] is not None else '',
                                        'icmp_type': test_data['icmp_type'] if test_data['icmp_type'] is not None else '',
                                        'icmp_code': test_data['icmp_code'] if test_data['icmp_code'] is not None else '',
                                        'destination_ip': ip_information['destinations'][cmd_index],
                                        'destination_port': test_data['destination_port'] if test_data['destination_port'] is not None else '',
                                        'expected_result': action,
                                        'execute': False,
                                        'command': '',
                                        'action': action
                                    })

                                    logger.error('Test record "{}" for interface "{}" marked to be skipped due to invalid addresses detection\n'.format(
                                        index, interface))

                        if command['list'] == False:

                            if ip_information['source']['result'] != False and ip_information['destination']['result'] != False:

                                self.testset.append({
                                    'test_record': index,
                                    'interface': interface,
                                    'protocol': test_data['protocol'],
                                    'source_ip': ip_information['source']['ip_address'],
                                    'source_port': test_data['source_port'] if test_data['source_port'] is not None else '',
                                    'icmp_type': test_data['icmp_type'] if test_data['icmp_type'] is not None else '',
                                    'icmp_code': test_data['icmp_code'] if test_data['icmp_code'] is not None else '',
                                    'destination_ip': ip_information['destination']['ip_address'],
                                    'destination_port': test_data['destination_port'] if test_data['destination_port'] is not None else '',
                                    'expected_result': action,
                                    'execute': True,
                                    'command': command['command'],
                                    'action': action
                                })
                                logger.info('Test record "{}" for interface "{}" stored for execution\n'.format(
                                    index, interface))

                            else:
                                self.testset.append({
                                    'test_record': index,
                                    'interface': interface,
                                    'protocol': test_data['protocol'],
                                    'source_ip': ip_information['source']['ip_address'],
                                    'source_port': test_data['source_port'] if test_data['source_port'] is not None else '',
                                    'icmp_type': test_data['icmp_type'] if test_data['icmp_type'] is not None else '',
                                    'icmp_code': test_data['icmp_code'] if test_data['icmp_code'] is not None else '',
                                    'destination_ip': ip_information['destination']['ip_address'],
                                    'destination_port': test_data['destination_port'] if test_data['destination_port'] is not None else '',
                                    'expected_result': action,
                                    'execute': False,
                                    'command': '',
                                    'action': action
                                })

                                logger.error('Test record "{}" for interface "{}" marked to be skipped due to invalid addresses detection\n'.format(
                                    index, interface))

        return self.testset

    def execute(self, testset, connect):
        '''
        The main brains of the operation.
        Called after the contruct methods
        '''

        for index, test_data in enumerate(testset):

            # process only tasks flagged for execution (True)
            # items flagged as False could not have IP Addresses resolved
            if test_data['execute'] == True:

                logger.info('Excuting: {} test record, "{}"'.format(
                    test_data['action'], test_data['test_record']))
                logger.info('Command: {}'.format(test_data['command']))

                cli_output = connect.send_command(test_data['command'])
                ParseData = ASAPolicyTest(self.script_dir, cli_output)
                test_results = ParseData.TestResult()

                # log to terminal the overall ASA action
                logger.info('Expecting: {}'.format(
                    test_data['expected_result']))
                logger.info('ASA reports: {}'.format(
                    test_results['action']))

                # if NAT is reported log to terminal
                if test_results['nat_rule'] is not None:
                    logger.debug('NAT detected: {} to {}'.format(
                        test_results['nat_from'], test_results['nat_to']))
                    logger.debug('NAT rule: "{}"'.format(
                        test_results['nat_rule']))

                # log to terminal the drop reason if it exists
                if test_results['drop_reason'] is not None:
                    logger.info('Drop reason: {}'.format(
                        test_results['drop_reason']))

                # log to terminal the test result
                if test_results['action'] == test_data['action']:
                    logger.info('Test passed!\n')
                    grade = '[PASS]'
                else:
                    logger.error('Test failed!\n')
                    grade = '[FAIL]'

                '''
                Store the test results
                '[{
                    command,
                    interface,
                    protocol,
                    source_ip,
                    source_port,
                    icmp_type,
                    icmp_code,
                    destination_ip,
                    destination_port,
                    action,
                    expected_result,
                    drop_reason,
                    nat_from,
                    nat_to,
                    nat_rule,
                    grade
                }]
                '''

                self.test_results.append({
                    'command': test_data['command'],
                    'interface': test_data['interface'],
                    'protocol': test_data['protocol'],
                    'source_ip': test_data['source_ip'],
                    'source_port': test_data['source_port'] if test_data['source_port'] is not None else '',
                    'icmp_type': test_data['icmp_type'] if test_data['icmp_type'] is not None else '',
                    'icmp_code': test_data['icmp_code'] if test_data['icmp_code'] is not None else '',
                    'destination_ip': test_data['destination_ip'],
                    'destination_port': test_data['destination_port'] if test_data['destination_port'] is not None else '',
                    'action': test_results['action'] if test_results['action'] is not None else '',
                    'expected_result': test_data['action'],
                    'drop_reason': test_results['drop_reason'] if test_results['drop_reason'] is not None else '',
                    'nat_from': test_results['nat_from'] if test_results['nat_from'] is not None else '',
                    'nat_to': test_results['nat_to'] if test_results['nat_to'] is not None else '',
                    'nat_rule': test_results['nat_rule'] if test_results['nat_rule'] is not None else '',
                    'grade': grade
                })
            else:
                self.test_results.append({
                    'command': test_data['command'],
                    'interface': test_data['interface'],
                    'protocol': test_data['protocol'],
                    'source_ip': test_data['source_ip'],
                    'source_port': test_data['source_port'] if test_data['source_port'] is not None else '',
                    'icmp_type': test_data['icmp_type'] if test_data['icmp_type'] is not None else '',
                    'icmp_code': test_data['icmp_code'] if test_data['icmp_code'] is not None else '',
                    'destination_ip': test_data['destination_ip'],
                    'destination_port': test_data['destination_port'] if test_data['destination_port'] is not None else '',
                    'action': '',
                    'expected_result': test_data['action'],
                    'drop_reason': '',
                    'nat_from': '',
                    'nat_to': '',
                    'nat_rule': '',
                    'grade': '[SKIP]'
                })
                logger.error('Skipping test record "{}" for interface "{}", invalid addresses detected\n'.format(
                    index, test_data['interface']))

        # append the loops test results to the jinja2 dictionary and return jinja2 dictionary to main.
        self.jinja2_results[test_data['interface']]['should_{}'.format(
            test_data['action'])] = self.test_results

        return self.jinja2_results
