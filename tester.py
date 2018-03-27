#!/usr/bin/env python3

'''
-*- coding: utf-8 -*-
title           : tester.py
description     : Converts the text files to structure YAML models
author          : donaldjohsnon.nz@gmail.com
date            : 15/03/2018
version         : 0.1
usage           : ./tester.py --help
notes           :
python_version  : 3.5.2
=======================================================================
'''

import sys
import os
import argparse
import yaml
import re
import datetime
from argparse import ArgumentParser
from getpass import getpass
from netmiko import ConnectHandler


from logzero import logger

from classes.structuredata import ASAPolicyTest
from classes.report import GenerateReport
from classes.search import RecursiveSearch
from classes.resolve import Resolve, Lookup

script_dir = os.path.dirname(os.path.realpath(__file__))


def CheckArgs(args=None):

    parser = argparse.ArgumentParser(
        description='TextFSM parser for Cisco command putputs')
    parser.add_argument('-i', '--host', required=True,
                        help='IP Address or hostname of Cisco ASA.')

    parser.add_argument('-u', '--username', required=True,
                        help='Priv 15 Username.')

    parser.add_argument('-s', '--ssh_port', required=False,
                        help='SSH port.', type=int, default=22)

    parser.add_argument('-y', '--yaml', required=True,
                        help='YAML file with tests.')

    parser.add_argument('-p', '--password', action='store_true', dest='password',
                        help='hidden password prompt')

    parser.add_argument('-e', '--enable_password', action='store_true', dest='enable_password',
                        help='hidden password prompt')

    parser.add_argument('-hf', '--hostfile', required=False,
                        help='absolute path to hostfile')

    results = parser.parse_args(args)

    if results.password:
        password = getpass()

    if results.enable_password:
        enable_password = getpass()
    else:
        enable_password = None

    return (
        results.host,
        results.ssh_port,
        results.yaml,
        results.username,
        password,
        enable_password,
        results.hostfile
    )


def ExecuteTests(action, context):
    '''
    Execute the cli packet tracer commands for each test and returns a list of dictionaries
    '''

    testing_results = []
    if action == 'allow':
        logger.info('Starting tests that should [PASS] block')
    elif action == 'drop':
        logger.info('Starting tests that should [FAIL] block')

    for index, test_data in enumerate(context[action]):

        logger.info('Processing {} protocol policy'.format(
            test_data['protocol'].lower()))

        # check that provided IP fields are IPs, if not attempt to resolve
        if hostfile_status == True:
            source_ip = Lookup(test_data['source_ip'], hostfile_status, hostfile_list)
            destination_ip = Lookup(test_data['destination_ip'], hostfile_status, hostfile_list)
        else:
            source_ip = Lookup(test_data['source_ip'], hostfile_status)
            destination_ip = Lookup(test_data['destination_ip'], hostfile_status)
        source_ip = source_ip.get_ip()
        destination_ip = destination_ip.get_ip()

        # start the test
        if re.match(r'(udp|tcp)', str(test_data['protocol'].lower())):

            command = 'packet-tracer input {} {} {} {} {} {} detail'.format(
                interface, test_data['protocol'], source_ip['ip_address'], test_data['source_port'], destination_ip['ip_address'], test_data['destination_port'])

        elif 'icmp' in str(test_data['protocol'].lower()):

            command = 'packet-tracer input {} {} {} {} {} {} detail'.format(
                interface, test_data['protocol'], source_ip['ip_address'], test_data['icmp_type'], test_data['icmp_code'], destination_ip['ip_address'])


        # Send the command to the ASA
        # only if the source and destination IPs are valid
        if source_ip['result'] != False and destination_ip['result'] != False:

            logger.info(
                'Processing: {} test, "{}"'.format(action, command))

            cli_output = connect.send_command(command)
            ParseData = ASAPolicyTest(script_dir, cli_output)
            test_results = ParseData.TestResult()

            # log to terminal the overall ASA action
            logger.info('ASA reports: {}'.format(
                test_results['action']))

            # if NAT is reported log to terminal
            if test_results['nat_rule'] is not None:
                logger.debug('NAT detected: {} to {}'.format(test_results['nat_from'], test_results['nat_to']))
                logger.debug('NAT rule: "{}"'.format(test_results['nat_rule']))

            # log to terminal the drop reason if it exists
            if test_results['drop_reason'] is not None:
                logger.info('Drop reason: {}'.format(
                    test_results['drop_reason']))

            # log to terminal the test result
            if test_results['action'] == action:
                logger.info('Test passed!\n')
                grade = '[PASS]'
            else:
                logger.error('Test failed!\n')
                grade = '[FAIL]'

            testing_results.append({
                'command': command,
                'interface': interface,
                'protocol': test_data['protocol'],
                'source_ip': source_ip['ip_address'],
                'source_port': test_data['source_port'] if test_data['source_port'] is not None else '',
                'icmp_type': test_data['icmp_type'] if test_data['icmp_type'] is not None else '',
                'icmp_code': test_data['icmp_code'] if test_data['icmp_code'] is not None else '',
                'destination_ip': destination_ip['ip_address'],
                'destination_port': test_data['destination_port'] if test_data['destination_port'] is not None else '',
                'action': test_results['action'] if test_results['action'] is not None else '',
                'expected_result': action,
                'drop_reason': test_results['drop_reason'] if test_results['drop_reason'] is not None else '',
                'nat_from': test_results['nat_from'] if test_results['nat_from'] is not None else '',
                'nat_to': test_results['nat_to'] if test_results['nat_to'] is not None else '',
                'nat_rule': test_results['nat_rule'] if test_results['nat_rule'] is not None else '',
                'grade': grade
            })
        else:
            testing_results.append({
                'command': command,
                'interface': interface,
                'protocol': test_data['protocol'],
                'source_ip': source_ip['ip_address'],
                'source_port': test_data['source_port'] if test_data['source_port'] is not None else '',
                'icmp_type': test_data['icmp_type'] if test_data['icmp_type'] is not None else '',
                'icmp_code': test_data['icmp_code'] if test_data['icmp_code'] is not None else '',
                'destination_ip': destination_ip['ip_address'],
                'destination_port': test_data['destination_port'] if test_data['destination_port'] is not None else '',
                'action': '',
                'expected_result': action,
                'drop_reason': '',
                'nat_from': '',
                'nat_to': '',
                'nat_rule': '',
                'grade': '[SKIP]'
            })
            logger.error('Skipping test record "{}" for interface "{}", invalid addresses detected\n'.format(index, interface))

    return testing_results


if __name__ == "__main__":

    # capture the passed arguments
    HOST, SSH_PORT, YAML_FILE, USERNAME, PASSWORD, ENABLE_PASSWORD, HOSTFILE = CheckArgs(
        sys.argv[1:])

    # construct the devi
    device = {
        'device_type': 'cisco_asa',
        'ip': HOST,
        'username': USERNAME,
        'password': PASSWORD,
        'port': SSH_PORT,
        'secret': ENABLE_PASSWORD,
        'verbose': False
    }

    # load the hostfile to a list
    try:
        hostfile_list = Resolve()
        hostfile_list = hostfile_list.load_hostfile(HOSTFILE)
        logger.info('Hostfile "{}" found and loaded'.format(HOSTFILE))
        hostfile_status = True
    except Exception:
        logger.error('Hostfile not loaded')
        hostfile_status = False
        pass

    # store the yaml tests
    with open('{}/tests/{}'.format(script_dir, YAML_FILE), 'r') as yml:
        test_map = yaml.safe_load(yml)

    # try:
    logger.info('Attempting connection to {}'.format(device['ip']))
    connect = ConnectHandler(**device)
    if connect:

        logger.info('Connected to {}\n'.format(device['ip']))

        results = {}
        # setup each interface dict
        for interface, test in test_map.items():
            results[interface] = {}

        # Begin the tests that should pass
        for interface, test in test_map.items():

            logger.info('Processing {} tests'.format(interface))

            # run each interfaces test and assign to dictionary
            if RecursiveSearch(test, 'allow'):
                results[interface]['should_allow'] = ExecuteTests('allow', test)

            if RecursiveSearch(test, 'drop'):
                results[interface]['should_drop'] = ExecuteTests('drop', test)

        print(results)
        GenerateReport(results, script_dir, datetime.datetime.now().strftime(
            "%d/%m/%Y @ %H:%M:%S"))

        # check for FAIL items and generate the retest YAML
        # save times with remediate rulesets
        # uses a recusive search to look for grade: [FAIL] in result dict
        # retest = RecursiveSearch(results, 'grade', '[FAIL]')

        # if retest == True:
        #     ReTest(results, script_dir)

    # except Exception:
    #     logger.error('{}: {}'.format(
    #         sys.exc_info()[0], sys.exc_info()[1]))
