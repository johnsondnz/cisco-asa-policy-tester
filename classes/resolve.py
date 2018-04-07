import sys
from logzero import logger
from socket import gethostbyname
from ipaddr import IPAddress


class Resolve(object):

    def load_hostfile(self, hostfile):

        with open(hostfile, 'r') as lookup:
            alist = [line.rstrip() for line in lookup]

        return alist

    def hostfile_lookup(self, host, hostfile=None):

        '''
        Parses the hostfile, if the object is found retuns the address, otherwise returns 'invalid'.
        '''

        # try:

        # search for the object
        for index, lookup_line in enumerate(hostfile):

            look_elements = lookup_line.split(' ')
            lookup_object = look_elements[2].lower()

            if str(host.lower()) == str(lookup_object.lower()):
                b_elembers = lookup_line.split(' ')
                object_ip = b_elembers[1]
                object_ip_found = True
                logger.debug('Found: {}, on line {}'.format(
                    lookup_line, index + 1))
                break
            else:
                object_ip_found = False

        if object_ip_found:
            logger.debug('Object: {}, IP: {}'.format(host, object_ip))
            return { 'lookup': 'success', 'ip_address': object_ip, 'lookup_type': 'hostfile' }
        else:
            logger.error('Object: {}, IP: not found'.format(host))
            object_ip = 'invalid'  # Need to return a string as ipaddr resolves False to 0.0.0.0
            return { 'lookup': 'failed', 'ip_address': object_ip, 'lookup_type': 'hostfile' }


        # except:
        #     logger.error('{}: {}'.format(
        #         sys.exc_info()[0], sys.exc_info()[1]))

    def dns(self, host):

        '''
        Returns the resoolved address or 'invalid' if resolution fails.
        '''

        try:
            resolved_address = gethostbyname(host)
            logger.debug(
                'DNS resovled object "{}" to "{}"'.format(host, resolved_address))
            return { 'lookup': 'success', 'ip_address': resolved_address, 'lookup_type': 'dns' }
        except Exception:
            logger.error(
                'DNS resolution failed for object "{}"'.format(host))
            return { 'lookup': 'failed', 'ip_address': host, 'lookup_type': 'dns' }
            
class Lookup(object):

    def __init__(self, validate_address, hostfile_status=False, hostfile_list=None):

        self.validate_address = validate_address
        self.hostfile_status = hostfile_status
        self.hostfile_list = hostfile_list

    def validate_ip(self, check_ip=None, recheck=False):

        '''
        This method ultimately returns the IP address for use in the commandset
        '''

        # if check_ip is set then use that instead
        validate_address = check_ip if check_ip != None else self.validate_address

        try:
            ip_address = validate_address if IPAddress(validate_address) else False
            logger.debug(
                'Source IP "{}" is a valid IP, further resolution not required\n'.format(validate_address))
            return { 'result': True, 'ip_address': ip_address }
        except ValueError:
            if recheck == False:
                logger.error(
                    'Source IP "{}" is not a valid IP, further resolution required'.format(validate_address))
            else:
                logger.error(
                    'Unable to resolve "{}" to an IP Address\n'.format(validate_address))
            return { 'result': False, 'ip_address': validate_address }

        

    def get_ip(self):

        # First check if string is a valid IP, for so return immediately
        results = self.validate_ip()
        if results['result'] == True:
            return { 'result': True, 'ip_address': results['ip_address'] }

        # Address is not valid IP, now resolve
        else:

            resolv = Resolve()

            # check the loaded hostfile, if it is loaded, if no hostfile fallback to dns
            if self.hostfile_status == True and self.hostfile_list != None:
                logger.debug('Looking up "{}" in hostfile'.format(self.validate_address))
                results = resolv.hostfile_lookup(self.validate_address, self.hostfile_list)

            # check results
            if results['lookup'] == 'success':
                pass
            else:
                # fallback to dns
                logger.debug('Attemping to resolve "{}" via DNS'.format(self.validate_address))
                results = resolv.dns(self.validate_address)

        # validate the address one more time before passing back
        if self.validate_ip(results['ip_address'], True)['result'] == True:
            return { 'result': True, 'ip_address': results['ip_address'] }
        else:
            return { 'result': False, 'ip_address': self.validate_address, 'msg': 'Unable to resolve address' }
