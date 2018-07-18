'''
The TextFSM class for parsing CLI outputs.
'''

import textfsm
from logzero import logger

def FileToMultiLineString(cli_output):
        
    '''
    Take the file and convert it to a mutliline string.
    '''
    
    data = ''.join(line for line in cli_output)
    return data

class TextFSMParser(object):
    
    def __init__(self, cli_output, template):

        '''
        Initiate the variables.
        '''

        self.cli_output = cli_output
        self.template = template

    def Parser(self):
        
        '''
        Create the table and return headers and values.
        '''

        with open(self.template, 'r') as template:
            re_table = textfsm.TextFSM(template)
        results = re_table.ParseText(self.cli_output)
        headers = ', '.join(re_table.header)
        
        mydict = {
            'headers': headers,
            'results': results
        }
        
        return  mydict
