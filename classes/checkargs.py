import argparse
from argparse import ArgumentParser
from getpass import getpass

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