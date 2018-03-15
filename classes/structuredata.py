from .parser import TextFSMParser, FileToMultiLineString
from logzero import logger
import re


class ASAPolicyTest(object):

    '''
    Class for parsing "show ip route connected".
    Uses TextFSM template to render text to YAML.
    '''

    def __init__(self, script_dir, cli_output):
        '''
        Input is the raw text output from Cisco IOS cli.
        '''

        self.name = 'asa_packet_tracer'
        self.template = '{}/templates_textfsm/{}'.format(script_dir, self.name)

        # Make sure the imput_file is converted to a multiline string
        self.cli_output = FileToMultiLineString(cli_output)

        # prep the data for parser processing
        self.parsed_data = TextFSMParser(self.cli_output, self.template)

    def TestResult(self):

        # loop through the prase textfsm data
        for line in self.parsed_data.Parser()['results']:

            # setup the columns
            input_interface = line[0] \
                if line[0] != '' else None

            input_interface_status = line[1] \
                if line[1] != '' else None

            input_interface_line_status = line[2] \
                if line[2] != '' else None

            output_interface = line[3] \
                if line[3] != '' else None

            output_interface_status = line[4] \
                if line[4] != '' else None

            output_interface_line_status = line[5] \
                if line[5] != '' else None

            action = line[6] \
                if line[6] != '' else None

            drop_reason = line[7] \
                if line[7] != '' else None

            mydict = {
                'input_interface': input_interface,
                'input_interface_status': input_interface_status,
                'input_interface_line_status': input_interface_line_status,
                'output_interface': output_interface,
                'output_interface_status': output_interface_status,
                'output_interface_line_status': output_interface_line_status,
                'action': action,
                'drop_reason': drop_reason
            }
            
            return mydict
