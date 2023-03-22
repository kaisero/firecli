from typing import Dict

import jsonschema

PATTERN_IPV4_ADDRESS = r'^((25[0-5]|(2[0-4]|1[0-9]|[1-9]|)[0-9])(\.(?!$)|$)){4}$'
PATTERN_IPV4_PREFIX = (
    r'^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}'
    r'([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/([0-9]|[1-2][0-9]|3[0-2]))$'
)
PATTERN_IPV4_RANGE_WITH_NETMASK = r'\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)' \
                                  r'\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)' \
                                  r'\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)' \
                                  r'\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/(?:3[0-2]|[12]?[0-9])\b'
PATTERN_IPV4_RANGE_LAZY = r'^[0-9a-zA-Z\/._-]{1,64}$'
PATTERN_OBJECT_NAME = r'^[0-9a-zA-Z._-]{1,64}$'
PATTERN_DEVICE_OR_DOMAIN = r'^[0-9a-zA-Z\._\-/]{1,64}$'
PATTERN_TIMEZONE = r'^[a-zA-Z0-9\/\_]{1,64}$'


def _schema(name: str):
    schema_map = {
        'object.override.import.src': {
            'type': 'object',
            'properties': {
                'objects': {
                    'type': 'object',
                    'properties': {},
                    'anyOf': [
                        {'required': ['dnsservergroups']},
                        {'required': ['hosts']},
                        {'required': ['ipv4addresspools']},
                        {'required': ['networks']},
                        {'required': ['networkgroups']},
                        {'required': ['ranges']},
                        {'required': ['timezones']},
                        {'required': ['urls']},
                    ],
                }
            },
            'required': ['objects'],
        },
        'object.dnsservergroup.override.import.src': {
            'type': 'object',
            'properties': {
                'objects': {
                    'type': 'object',
                    'properties': {
                        'dnsservergroups': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'required': ['name', 'overrides'],
                                'properties': {
                                    'name': {'type': 'string', 'pattern': PATTERN_OBJECT_NAME},
                                    'overrides': {
                                        'type': 'array',
                                        'minItems': 1,
                                        'items': {
                                            'type': 'object',
                                            'required': ['target', 'values'],
                                            'properties': {
                                                'target': {'type': 'string', 'pattern': PATTERN_DEVICE_OR_DOMAIN},
                                                'values': {
                                                    'type': 'array',
                                                    'minItems': 1,
                                                    'items': {'type': 'string', 'pattern': PATTERN_IPV4_ADDRESS},
                                                },
                                            },
                                        },
                                    },
                                },
                            },
                        }
                    },
                    'required': ['dnsservergroups'],
                }
            },
            'required': ['objects'],
        },
        'object.host.override.import.src': {
            'type': 'object',
            'properties': {
                'objects': {
                    'type': 'object',
                    'properties': {
                        'hosts': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'required': ['name', 'overrides'],
                                'properties': {
                                    'name': {'type': 'string', 'pattern': PATTERN_OBJECT_NAME},
                                    'overrides': {
                                        'type': 'array',
                                        'minItems': 1,
                                        'items': {
                                            'type': 'object',
                                            'required': ['target', 'value'],
                                            'properties': {
                                                'target': {'type': 'string', 'pattern': PATTERN_DEVICE_OR_DOMAIN},
                                                'value': {'type': 'string', 'pattern': PATTERN_IPV4_ADDRESS},
                                            },
                                        },
                                    },
                                },
                            },
                        }
                    },
                    'required': ['hosts'],
                }
            },
            'required': ['objects'],
        },
        'object.ipv4addresspool.override.import.src': {
            'type': 'object',
            'properties': {
                'objects': {
                    'type': 'object',
                    'properties': {
                        'ipv4addresspools': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'required': ['name', 'overrides'],
                                'properties': {
                                    'name': {'type': 'string', 'pattern': PATTERN_OBJECT_NAME},
                                    'overrides': {
                                        'type': 'array',
                                        'minItems': 1,
                                        'items': {
                                            'type': 'object',
                                            'required': ['target', 'value'],
                                            'properties': {
                                                'target': {'type': 'string', 'pattern': PATTERN_DEVICE_OR_DOMAIN},
                                                'value': {'type': 'string', 'pattern': PATTERN_IPV4_RANGE_LAZY},
                                            },
                                        },
                                    },
                                },
                            },
                        }
                    },
                    'required': ['ipv4addresspools'],
                }
            },
            'required': ['objects'],
        },
        'object.network.override.import.src': {
            'type': 'object',
            'properties': {
                'objects': {
                    'type': 'object',
                    'properties': {
                        'networks': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'required': ['name', 'overrides'],
                                'properties': {
                                    'name': {'type': 'string', 'pattern': PATTERN_OBJECT_NAME},
                                    'overrides': {
                                        'type': 'array',
                                        'minItems': 1,
                                        'items': {
                                            'type': 'object',
                                            'required': ['target', 'value'],
                                            'properties': {
                                                'target': {'type': 'string', 'pattern': PATTERN_DEVICE_OR_DOMAIN},
                                                'value': {'type': 'string', 'pattern': PATTERN_IPV4_PREFIX},
                                            },
                                        },
                                    },
                                },
                            },
                        }
                    },
                    'required': ['networks'],
                }
            },
            'required': ['objects'],
        },
        'object.networkgroup.override.import.src': {
            'type': 'object',
            'properties': {
                'objects': {
                    'type': 'object',
                    'properties': {
                        'networkgroups': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'required': ['name', 'overrides'],
                                'properties': {
                                    'name': {'type': 'string', 'pattern': PATTERN_OBJECT_NAME},
                                    'overrides': {
                                        'type': 'array',
                                        'minItems': 1,
                                        'items': {
                                            'type': 'object',
                                            'required': ['target', 'values'],
                                            'properties': {
                                                'target': {'type': 'string', 'pattern': PATTERN_DEVICE_OR_DOMAIN},
                                                'values': {'type': 'array', 'minItems': 1, 'items': {'type': 'string'}},
                                            },
                                        },
                                    },
                                },
                            },
                        }
                    },
                    'required': ['networkgroups'],
                }
            },
            'required': ['objects'],
        },
        'object.range.override.import.src': {
            'type': 'object',
            'properties': {
                'objects': {
                    'type': 'object',
                    'properties': {
                        'ranges': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'required': ['name', 'overrides'],
                                'properties': {
                                    'name': {'type': 'string', 'pattern': PATTERN_OBJECT_NAME},
                                    'overrides': {
                                        'type': 'array',
                                        'minItems': 1,
                                        'items': {
                                            'type': 'object',
                                            'required': ['target', 'value'],
                                            'properties': {
                                                'target': {'type': 'string', 'pattern': PATTERN_DEVICE_OR_DOMAIN},
                                                'value': {'type': 'string'},
                                            },
                                        },
                                    },
                                },
                            },
                        }
                    },
                    'required': ['ranges'],
                }
            },
            'required': ['objects'],
        },
        'object.timezone.override.import.src': {
            'type': 'object',
            'properties': {
                'objects': {
                    'type': 'object',
                    'properties': {
                        'timezones': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'required': ['name', 'overrides'],
                                'properties': {
                                    'name': {'type': 'string', 'pattern': PATTERN_OBJECT_NAME},
                                    'overrides': {
                                        'type': 'array',
                                        'minItems': 1,
                                        'items': {
                                            'type': 'object',
                                            'required': ['target', 'value'],
                                            'properties': {
                                                'target': {'type': 'string', 'pattern': PATTERN_DEVICE_OR_DOMAIN},
                                                'value': {'type': 'string', 'pattern': PATTERN_TIMEZONE},
                                            },
                                        },
                                    },
                                },
                            },
                        }
                    },
                    'required': ['timezones'],
                }
            },
            'required': ['objects'],
        },
        'object.url.override.import.src': {
            'type': 'object',
            'properties': {
                'objects': {
                    'type': 'object',
                    'properties': {
                        'urls': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'required': ['name', 'overrides'],
                                'properties': {
                                    'name': {'type': 'string', 'pattern': PATTERN_OBJECT_NAME},
                                    'overrides': {
                                        'type': 'array',
                                        'minItems': 1,
                                        'items': {
                                            'type': 'object',
                                            'required': ['target', 'value'],
                                            'properties': {
                                                'target': {'type': 'string', 'pattern': PATTERN_DEVICE_OR_DOMAIN},
                                                'value': {'type': 'string'},
                                            },
                                        },
                                    },
                                },
                            },
                        }
                    },
                    'required': ['urls'],
                }
            },
            'required': ['objects'],
        },
    }
    schema_map['object.override.import.src']['properties']['objects']['properties'] = {
        'dnsservergroups': schema_map['object.dnsservergroup.override.import.src']['properties']['objects'][
            'properties']['dnsservergroups'],
        'hosts': schema_map['object.host.override.import.src']['properties']['objects']['properties']['hosts'],
        'ipv4addresspools': schema_map['object.ipv4addresspool.override.import.src']['properties']['objects'][
            'properties']['ipv4addresspools'],
        'networks': schema_map['object.network.override.import.src']['properties']['objects']['properties']['networks'],
        'networkgroups': schema_map['object.networkgroup.override.import.src']['properties']['objects'][
            'properties']['networkgroups'],
        'ranges': schema_map['object.range.override.import.src']['properties']['objects']['properties']['ranges'],
        'timezones': schema_map['object.timezone.override.import.src']['properties']['objects'][
            'properties']['timezones'],
        'urls': schema_map['object.url.override.import.src']['properties']['objects']['properties']['urls'],
    }
    return schema_map[name]


def validate(json: Dict, path: str):
    jsonschema.validate(instance=json, schema=_schema(path))
