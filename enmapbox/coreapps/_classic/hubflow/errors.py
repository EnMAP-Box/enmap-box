class HubFlowError(Exception):
    pass

class FlowObjectPickleFileError(HubFlowError):
    '''File is not a valid pickle file.'''

class FlowObjectTypeError(HubFlowError):
    '''Wrong flow object type.'''