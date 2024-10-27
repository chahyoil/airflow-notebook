# helpers/constants.py
DATABRICKS_WORKSPACES = {
    'workspace1': 'workspace_id_1'
}

NOTEBOOK_IDS = {
    'notebook1': 'notebook_id_1',
    'notebook2': 'notebook_id_2',
    'notebook3': 'notebook_id_3',
    'notebook4': 'notebook_id_4',
    'notebook5': 'notebook_id_5',
    'notebook6': 'notebook_id_6',
    'notebook7': 'notebook_id_7',
    'notebook8': 'notebook_id_8',
    'notebook9': 'notebook_id_9',
    'notebook10': 'notebook_id_10',
    'notebook11': 'notebook_id_11',
    'notebook12': 'notebook_id_12',
    'notebook13': 'notebook_id_13',
    'notebook14': 'notebook_id_14',
    'notebook15': 'notebook_id_15',
    'notebook16': 'notebook_id_16',
    'notebook17': 'notebook_id_17',
    'notebook18': 'notebook_id_18',
    'notebook19': 'notebook_id_19',
    'notebook20': 'notebook_id_20', 
    'notebook21': 'notebook_id_21',
    'notebook22': 'notebook_id_22',
    'notebook23': 'notebook_id_23',
    'notebook24': 'notebook_id_24',
    'notebook25': 'notebook_id_25',
    'notebook26': 'notebook_id_26',
    'notebook27': 'notebook_id_27',
    'notebook28': 'notebook_id_28',
    'notebook29': 'notebook_id_29',
}

NOTEBOOK_CONFIG = {
    'notebook1': {
        'id': 'notebook_id_1',
        'params': {
            'param1': 'value1',
            'param2': 'value2'
        }
    },
    'notebook2': {
        'id': 'notebook_id_2',
        'params': {
            'param1': 'value3',
            'param2': 'value4'
        }
    },
    'notebook3': {
        'id': 'notebook_id_3',
        'params': {
            'param1': 'value5',
            'param2': 'value6'
        }
    },
    'notebook4': {
        'id': 'notebook_id_4',
        'params': {
            'param1': 'value7',
            'param2': 'value8'
        }
    },
    # ... 나머지 노트북들에 대해서도 같은 구조로 계속 ...
    'notebook29': {
        'id': 'notebook_id_29',
        'params': {
            'param1': 'value57',
            'param2': 'value58'
        }
    }
}

def get_notebook_id(notebook_name):
    return NOTEBOOK_IDS.get(notebook_name)

def get_notebook_config(notebook_name):
    return NOTEBOOK_CONFIG.get(notebook_name)

USER_DEFINED_MACROS = {
    'get_notebook_id': get_notebook_id,
    'get_notebook_config': get_notebook_config
}
