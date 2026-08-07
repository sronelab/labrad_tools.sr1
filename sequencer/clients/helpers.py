from itertools import chain

class ConfigWrapper(object):
    def __init__(self, **config_entries):
        self.__dict__.update(config_entries)

def merge_dicts(*dictionaries):
    merged_dictionary = {}
    for d in dictionaries:
        merged_dictionary.update(d)
    return merged_dictionary

def get_sequence_parameters(x):
    """ determine which parameters we need to get from conductor or db """
    if isinstance(x, str):
        return {x} if x.startswith('*') else set()
    elif isinstance(x, (list, tuple)):
        return {param for item in x for param in get_sequence_parameters(item)}
    elif isinstance(x, dict):
        return {param for value in x.values() for param in get_sequence_parameters(value)}
    else:
        return set()

def substitute_sequence_parameters(x, parameter_values):
    if isinstance(x, str):
        if x.startswith('*'):
            return parameter_values.get(x, 0)
        return x
        
    elif isinstance(x, list):
        return [substitute_sequence_parameters(xx, parameter_values) for xx in x]
        
    elif isinstance(x, dict):
        return {k: substitute_sequence_parameters(v, parameter_values) for k, v in x.items()}
        
    return x
