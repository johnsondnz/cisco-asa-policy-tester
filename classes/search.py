from logzero import logger


def RecursiveSearch(data, find_key, *args):
    # logger.debug('searching for key {}'.format(find_key))
    if find_key in data:
        # logger.debug('found {} key'.format(find_key))
        # if a argument is submitted use it to check the located key
        # for a value matching the argument
        # otherwise this was a key-search only
        if args:
            # logger.debug('searching for value {}'.format(args[0]))
            value_search = args[0]
            if value_search in data[find_key]:
                # logger.debug('found {} in {}'.format(value_search, find_key))
                return True
        else:
            return True
    else:
        for key, value in data.items():
            if isinstance(value, dict):
                # logger.debug('{} is a dict'.format(key))
                test = RecursiveSearch(value, find_key)
                if test is True:
                    return test
            # test for a list
            elif isinstance(value, list):
                # logger.debug('{} is a list'.format(key))
                for data in value:
                    # logger.debug(data)
                    if isinstance(data, dict):
                        # logger.debug('{} is a dict'.format(data))
                        test = RecursiveSearch(data, find_key)
                        if test is True:
                            return test
            # can use this later to look at strings
            elif isinstance(value, str):
                # logger.debug('{} contains a string'.format(key))
                pass
    return False
