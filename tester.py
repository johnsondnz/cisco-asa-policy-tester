#!/usr/bin/env python3

'''
-*- coding: utf-8 -*-
title           : tester.py
description     : Converts the text files to structure YAML models
author          : donaldjohsnon.nz@gmail.com
date            : 27/03/2018
version         : 0.4
usage           : ./tester.py --help
notes           :
python_version  : 3.5.2
=======================================================================
'''

import sys
import os
import yaml
import re
import datetime
from netmiko import ConnectHandler


from logzero import logger

from classes.report import GenerateReport
from classes.resolve import Resolve
from classes.testcontrol import TestControl
from classes.checkargs import CheckArgs

script_dir = os.path.dirname(os.path.realpath(__file__))

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

    
    # try:
    # store the yaml tests
    with open('{}/tests/{}'.format(script_dir, YAML_FILE), 'r') as yml:
        yaml_data = yaml.safe_load(yml)

    test_control = TestControl(script_dir, yaml_data, hostfile_status, hostfile_list)  # call TestControl
    testset = test_control.construct_testset()   # Build testset

    logger.info('Attempting connection to {}'.format(device['ip']))


    connect = ConnectHandler(**device)
    if connect:
        results = test_control.execute(testset, connect)

    GenerateReport(results, script_dir, datetime.datetime.now().strftime(
        "%d/%m/%Y @ %H:%M:%S"))

    # except Exception:
    #     logger.error('{}: {}'.format(sys.exc_info()[0], sys.exc_info()[1:]))
