import yaml
from .search import RecursiveSearch
from .resolve import Lookup
from logzero import logger
import re


class Validate(object):

    '''
    Class that pre-validates all YAML defined tests prior to data model creatation and test execution
    Provides feedback on YAML data strcuture to prevent wasted time on long runs
    Flow:
    
    call `run_validation`
    This method will call other class methods in the following order.
        1. unmonitored = self._test_unmonitored_keys(test_data)         # Checks for unmonitored keys in YAML file.
        2. missing_keys = self._test_validate_keys_exist(test_data)     # Checks for missing registered keys in YAML file.
        3. invalid_instances = self._test_validate_instances(test_data) # Uses isinstance to verify the data is the correct structure.
        4. test_values = self._test_validate_values(test_data)          # Check the values in the instances is the correct type and is valid.
        5. self._validation_storage(*args)                              # called once for data obtained in steps 1-4, stores all the data required for steps 6-7.
        6. self._confirm_results()                                      # Recusively searches the validation data saved in step 5 for failed validation and sets aggregated pass/fail
        7. self._pass_or_raise_exception()                              # outputs issues to the terminal and raises an exception, only if step 6 determines failure of a testlet

    example:
    validate = Validate(dir, yaml_file, hostfile_status=True, hostfile_list=hostlist)
    validation = validate.run_validation()

    the above example will only output data if an data strucutre error is detected
    if this occurs an exception is raised and the program exits

    if there is no error detected, then there is no exception and the program continues
    an info log is printed to the terminal to advise if validation was successful
    '''

    def __init__(self, script_dir, yaml_data, hostfile_status=False, hostfile_list=None):

        self.yaml_data = yaml_data

        # grab the hostfile information
        self.hostfile_status = hostfile_status
        self.hostfile_list = hostfile_list

        # register the monitored keys
        self.registered_keys = ['protocol', 'source_ip', 'source_port', 'destination_ip',
                              'destination_port', 'icmp_code', 'icmp_type', 'expected_result']

        # load registered protocols
        self.registered_protocols = ['udp', 'icmp', 'tcp', 'esp']

        # initiate test storage
        self.validation = {}
        self.validation['results'] = ''

    def run_validation(self):
        '''
        Loads YAML and check data structures
        Returns a dictionary

        {
            results: boolean
            interface: { 
                testlets: [
                    {
                        testlet_id: int,
                        result: boolean,
                        issues: {
                            invalid_keys: [],
                            missing_keys: [],
                            invalid_instances: [(),()], # list of tuple pairs
                            invalid_data: [(),()]       # list of tuple pairs
                        },
                        yaml: dict
                        }
                    },
                    {
                        testlet_id: int,
                        result: boolean,
                        issues: {
                            invalid_keys: [],
                            missing_keys: [],
                            invalid_instances: [(),()], # list of tuple pairs
                            invalid_data: [(),()]       # list of tuple pairs
                        },
                        yaml: dict
                        }
                    }
                ]
            }
        }
        '''

        logger.debug('Stepped into run_validation')
        logger.info('Beginning testlet validation')

        for interface, item in self.yaml_data.items():

            logger.debug(
                'Validating testlets for interface: {}'.format(interface))

            self.validation[interface] = {}
            self.validation[interface]['testlets'] = []

            # iterate through the action list
            for index, test_data in enumerate(item):

                # setup testlet validation storage
                self.validation[interface]['testlets'].append({
                    'testlet_id': index,
                    'yaml': test_data
                })
                self.validation[interface]['testlets'][index]['issues'] = {}
                self.validation[interface]['testlets'][index]['issues']['invalid_keys'] = []
                self.validation[interface]['testlets'][index]['issues']['missing_keys'] = []
                self.validation[interface]['testlets'][index]['issues']['invalid_instances'] = []
                self.validation[interface]['testlets'][index]['issues']['invalid_data'] = []

                # Check this testlets data
                unmonitored = self._test_unmonitored_keys(test_data)
                missing_keys = self._test_validate_keys_exist(test_data)
                invalid_instances = self._test_validate_instances(test_data)
                test_values = self._test_validate_values(test_data)

                # store the testlet validation results
                self._validation_storage(
                    interface, index, 'invalid_keys', unmonitored)
                self._validation_storage(
                    interface, index, 'missing_keys', missing_keys)
                self._validation_storage(
                    interface, index, 'invalid_instances', invalid_instances)
                self._validation_storage(
                    interface, index, 'invalid_data', test_values)

                # set the final grade
                self._confirm_results()

                # run the results through the exception handler
                # if all is good it will return True
                # otherwise it will construct the exception for user remedy and exit(1)
                self._pass_or_raise_exception()

    def _test_validate_keys_exist(self, testlet_data):
        '''
        Checks that all the keys are registed for the testlet
        {
            results: boolean,
            errored_keys: [],
        }
        '''

        logger.debug('Stepped into _test_validate_keys_exist')
        logger.debug('Asserting registered keys exist')

        results = {}
        results['result'] = True
        results['errored_keys'] = []

        # First check all the keys exist
        for key in self.registered_keys:

            # validate all keys exist
            validate_key_exists = RecursiveSearch(testlet_data, key)

            if validate_key_exists == False:
                results['result'] = False
                results['errored_keys'].append(key)
            else:
                # Only set 'results' key to True if it is not already False
                results['result'] = True if results['result'] != False else True

        logger.debug('Results: {}'.format(results))
        return results

    def _test_unmonitored_keys(self, testlet_data):
        '''
        Checks for keys that are unmonitored, provides warning
        {
            results: boolean,
            errored_keys: [],
        }
        '''

        logger.debug('Stepped into _test_unmonitored_keys')
        logger.debug('Checking for unmonitored keys')

        results = {}
        results['result'] = True
        results['unmonitored_keys'] = []
        results['testlet'] = {}

        # work with dictionary values as tuples
        # loop through the testlet tuple pairs
        for tp in testlet_data.items():
            key = tp[0]

            if key not in self.registered_keys:
                results['result'] == False
                results['errored_keys'].append(key)
            else:
                # Only set 'results' key to True if it is not already False
                results['result'] = True if results['result'] == True else False

        logger.debug('Results: {}'.format(results))
        return results

    def _test_validate_instances(self, testlet_data):
        '''
        Check the key value is the correct instance type and contains a value or any type
        Retuns a simple dictionary
        {
            results: boolean,
            errored_keys: [],
        }
        '''

        logger.debug('Stepped into _test_validate_instances')
        logger.debug('Asserting instance types')

        def _instance_types(key, value, key_list):
            '''
            Takes the expected key_list and valdaites that it is of the correct type
            Returns a simple True/False
            '''

            logger.debug(
                'Stepped into _test_validate_instances._instance_types')

            strings_or_lists = ['source_ip', 'source_port',
                                'destination_ip', 'destination_port']
            string_or_integers = ['protocol']
            strings = ['expected_result']
            integers = ['icmp_type', 'icmp_code']

            # Verify that key_list is a list
            # Used to pickup programming errors, not user error
            try:
                isinstance(key, list)
            except Exception:
                logger.error('Submited keys are not a list')

            if key in strings_or_lists and key in key_list:
                result = True if isinstance(key, str) or isinstance(
                    key, list) and value is not None else False

            if key in strings and key in key_list:
                result = True if isinstance(
                    key, str) and value is not None else False

            if key in integers and key in key_list:
                result = True if isinstance(
                    key, int) and value is not None else False

            if key in string_or_integers and key in key_list:
                result = True if isinstance(key, str) or isinstance(
                    key, int) and value is not None else False

            logger.debug('Results: {}'.format(results))
            return result

        results = {}
        results['result'] = True
        results['errored_keys'] = []

        # work with dictionary values as tuples
        # loop through the testlet tuple pairs
        for tp in testlet_data.items():
            key = tp[0]
            value = tp[1]

            logger.debug('{} = {}'.format(key, value))

            if key == 'protocol' and value.lower() == 'icmp':

                result = _instance_types(
                    key, value,
                    ['protocol', 'expected_result', 'icmp_type',
                        'icmp_code', 'source_ip', 'destination_ip']
                )

            elif key == 'protocol' and re.match(r'(udp|tcp|esp)', str(value.lower())):

                result = _instance_types(
                    key, value,
                    ['protocol', 'expected_result', 'source_ip',
                        'source_port', 'destination_ip', 'destination_port']
                )

            if result == False:
                results['result'] = False
                # append key,value tuple pair to the list
                results['errored_keys'].append((key, value))
            else:
                # Only set 'results' key to True if it is not already False
                results['result'] = True if results['result'] != False else True

        logger.debug('Results: {}'.format(results))
        return results

    def _test_validate_values(self, testlet_data):
        '''
        Check the provided value is a valid type for the key
        ports between 0:65535
        ipaddr is an ip_address (dns/hostfile resolution will be performed as required)
        expected_result is either 'drop|allow'
        icmp type/code combination is valid (well it checks the range, but not the pairing, at this stage)
        protocol is a registed value
        {
            results: boolean,
            errored_keys: [],
        }
        '''

        logger.debug('Stepped into _test_validate_values')
        logger.debug('Asserting key values are as per definition')

        def _set_result(key, value):
            '''set results, cause I'm lazy'''
            results['result'] = False
            # append key,value tuple pair to the list
            results['errored_keys'].append((key, value))

        results = {}
        results['result'] = True
        results['errored_keys'] = []

        for tp in testlet_data.items():
            key = tp[0]
            value = tp[1]

            # check protocol is registered by application
            if key == 'protocol':
                if value in self.registered_protocols:
                    # Only set 'results' key to True if it is not already False
                    results['result'] = True if results['result'] != False else True
                else:
                    _set_result(key, value)

            if key == 'expected_result':
                if re.match(r'(drop|allow)', str(value.lower())):
                    # Only set 'results' key to True if it is not already False
                    results['result'] = True if results['result'] != False else True
                else:
                    _set_result(key, value)

            if re.match(r'(icmp_type|icmp_code)', str(key.lower())):
                if value >= 0 and value <= 254:
                    # Only set 'results' key to True if it is not already False
                    results['result'] = True if results['result'] != False else True
                else:
                    _set_result(key, value)

            # process ports which could be a str or a list
            if re.match(r'(source_port|destination_port)', str(key.lower())) and isinstance(key, str):
                if value >= 0 and value <= 65535:
                    # Only set 'results' key to True if it is not already False
                    results['result'] = True if results['result'] != False else True
                else:
                    _set_result(key, value)
            elif re.match(r'(source_port|destination_port)', str(key.lower())) and isinstance(key, list):
                for port in value:
                    if port >= 0 and port <= 65535:
                        # Only set 'results' key to True if it is not already False
                        results['result'] = True if results['result'] != False else True
                    else:
                        _set_result(key, port)

            # process ip_addresses which could be a str or a list
            if re.match(r'(source_ip|destination_ip)', str(key.lower())) and isinstance(key, str):
                ip_lookup = Lookup(
                    value, self.hostfile_status, self.hostfile_list)
                ip_address = ip_lookup.get_ip()
                if ip_address['result'] == True:
                    # Only set 'results' key to True if it is not already False
                    results['result'] = True if results['result'] != False else True
                else:
                    _set_result(key, value)
            elif re.match(r'(source_ip|destination_ip)', str(key.lower())) and isinstance(key, list):
                for ip in value:
                    ip_lookup = Lookup(
                        ip, self.hostfile_status, self.hostfile_list)
                    ip_address = ip_lookup.get_ip()
                    if ip_address['result'] == True:
                        # Only set 'results' key to True if it is not already False
                        results['result'] = True if results['result'] != False else True
                    else:
                        _set_result(key, value)

        logger.debug('Results: {}'.format(results))
        return results

    def _validation_storage(self, interface, index, storage, testlet_data):
        '''
        Runs the test.
        index is the list number for this testlet
        interface is the interface
        storage is the place the inalid items are appended to
        testlet_data is the results of the check from either:
            - self._test_unmonitored_keys
            - self._test_validate_keys_exist
            - self._test_validate_instances
        'errored_keys' is the standard value returned by the above tests
        everything is stored in self.validation
        '''

        logger.debug('Stepped into _validation_storage')

        if testlet_data['result'] == False:
            self.validation[interface]['testlets'][index]['result'] = False
            self.validation[interface]['testlets'][index]['issues'][storage].append(
                testlet_data['errored_keys'])
            self.validation[interface]['testlets'][index]['yaml'] = testlet_data
        else:
            self.validation[interface]['testlets'][index]['result'] = True

    def _confirm_results(self):
        '''
        Iterates through self.validation data and determine overall pass/fail grade
        '''

        logger.debug('Stepped into _confirm_results')

        # search self.validation for any key,value pair for result = False
        # if found set self.validation['results'] = False
        self.validation['results'] = False if RecursiveSearch(
            self.validation, 'result', False) == True else False

    def _pass_or_raise_exception(self):
        '''
        Raises an exception if any of the tests fail.
        Loops through the entire self.validation dictionary and provides a report
        on failure.
        '''

        logger.debug('Stepped into _pass_or_raise_exception')

        # Check the overall result which will indicate issues with a testlet
        if self.validation['results'] == False:

            # iterface through the validation_data for the interfaces testlets
            for interface, testlets in self.validation.items():

                # iterate through each testlet
                for testlet_validation_data in testlets:

                    # if the testlet is at fault, output the information
                    if testlet_validation_data['result'] == False:

                        logger.error('Something went wring with: Interface: {}, testlet_id: {}'.format(
                            interface, testlet_validation_data['testlet_id']))
                        logger.error('YAML: {}'.format(
                            testlet_validation_data['yaml']))
                        logger.error('{}'.format(
                            testlet_validation_data['issues']))
                        logger.error

            # raise th ValueError at the conclusion of the looping
            raise ValueError(
                'Check YAML data for above testlets, fix and rerun.')

        logger.info('All testlets passed data validation tests.')
