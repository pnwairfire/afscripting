__author__      = "Joel Dubowy"

import configparser
import copy
import datetime
import json
import logging
import os
import re
from argparse import (
    ArgumentTypeError, ArgumentParser, Action, RawTextHelpFormatter
)

from afdatetime.parsing import parse as parse_datetime
from afconfig import merge_configs, set_config_value

from .utils import exit_with_msg

__all__ = [
    # Argument Parsing
    'parse_args',
    # Argument Action Callbacks
    'SetConfigOptionAction',
    'ExtractAndSetKeyValueAction',
    'ParseDatetimeAction',
    'append_or_split_with_delimiter_and_extend',
    'AppendOrSplitAndExtendAction',
    'ConfigOptionAction',
    'BooleanConfigOptionAction',
    'IntegerConfigOptionAction',
    'FloatConfigOptionAction',
    'JSONConfigOptionAction',
    'ConfigFileAction'
]

##
## 'Public' Interface
##

##  Argument Parsing Methods

def parse_args(required_args, optional_args, positional_args=None, usage=None,
        epilog=None, post_args_outputter=None, pre_validation=None,
        support_configuration_options_short_names=False):
    """....

    Arguments:
     - required_args --
     - optional_args --
    Kwargs
     - usage -- usage text to replace default
     - epilog -- additional help text to display after list of args
     - post_args_outputter -- callable object that generates epilog
        (for when itneeds to be dynamically generated)
     - pre_validation -- callable object that performs any tasks that
        should be done before outputing the parsed args
     - support_configuration_options_short_names -- e.g. '-c', '-C', '-B', etc.

    TODO:
     - support custom positional args
    """
    parser = ArgumentParser(usage=usage)

    if epilog or post_args_outputter:
        parser.epilog = epilog or post_args_outputter()
        parser.formatter_class = RawTextHelpFormatter

    add_arguments(parser, required_args, required=True)
    add_arguments(parser, optional_args)
    if positional_args:
        add_arguments(parser, positional_args)

    add_logging_options(parser)
    add_configuration_options(parser,
        support_configuration_options_short_names)

    args = parser.parse_args()

    configure_logging_from_args(args, parser)

    if pre_validation:
        pre_validation(parser, args)

    output_args(args)

    return parser, args

## Callback Actions for add_argument

class SetConfigOptionAction(Action):

    OPTION_EXTRACTOR = re.compile('(\w+)\.(\w+)=(.+)')

    def __call__(self, parser, namespace, value, option_string=None):
        m = self.OPTION_EXTRACTOR.search(value.strip())
        if not m:
            msg = "Invalid value '%s' for option '%s' - value must be of the form 'Section.OPTION=value'" % (
                value, option_string)
            raise OptionValueError(msg)
        config = getattr(namespace, self.dest)
        if not config:
            config = configparser.ConfigParser()
            setattr(namespace, self.dest, config)
        if not config.has_section(m.group(1)):
            config.add_section(m.group(1))
        config.set(m.group(1), m.group(2), m.group(3))

class ExtractAndSetKeyValueAction(Action):

    KEY_VALUE_EXTRACTER = re.compile('^([^=]+)=([^=]+)$')

    def __call__(self, parser, namespace, value, option_string=None):
        """Splits value into key/value, and set in destination dict

        Note: Expects value to be of the format 'key=value'.  Also expects
        destination (i.e. parser.value's self.dest attribute), to be
        initialized as an empty dict.
        """
        m = self.KEY_VALUE_EXTRACTER.search(value.strip())
        if not m:
            msg = "Invalid value '%s' for option '%s' - value must be of the form 'key=value'" % (
                value, opt)
            raise ArgumentTypeError(msg)
        d = getattr(namespace, self.dest)
        d[m.group(1)] = m.group(2)

class ParseDatetimeAction(Action):

    def __call__(self, parser, namespace, value, option_string=None):
        """Parses datetime from string value

        Note: Expects value to be of one of the formats listed in
        afdatetime.parsing.RECOGNIZED_DATETIME_FORMATS
        """
        try:
            dt = parse_datetime(value)
        except ValueError:
            # If we got here, none of them matched, so raise error
            raise ArgumentTypeError("Invalid datetime format '%s' for option %s" % (
                value, option_string))
        setattr(namespace, self.dest, dt)


def append_or_split_with_delimiter_and_extend(dilimiter):
    """Generates a callback function that augments the append action with the
    ability to split a string and extend the redsulting values to the option array

    Args:
     - delimiter -- character used to to split the string string
    """
    class C(Action):
        def __call__(self, parser, namespace, values, option_string=None):
            d = getattr(namespace, self.dest)
            d.extend(values.split(dilimiter))
    return C
AppendOrSplitAndExtendAction = append_or_split_with_delimiter_and_extend(',')
"""For convenience, returns callback generated by
append_or_split_with_delimiter_and_extend with comma as the dilimiter
"""

## Configuration related

class ConfigOptionAction(Action):

    EXTRACTER = re.compile('^([^=]+)=([^=]+)$')

    def _cast_value(self, val):
        # default is to return as is (as str)
        return val

    def __call__(self, parser, namespace, value, option_string=None):
        """Set individual config option in config dict

        Note: Expects value to be of the format 'section.*.key=value', with
        any section nesting depth.

        TODO: come up with way to specify numeric and boolean values
          (maybe have separate option, e.g. '--int-config-option'; would
           need to do something like subclass ConfigOptionAction and
           have hook for setting value so that subclasses could used
           that hook to cast to int)
        """
        m = self.EXTRACTER.search(value.strip())
        if not m:
            msg = ("Invalid value '{}' for option '{}' - value must be of the "
                "form 'section.*.key=value'".format(value, option_string))
            raise ArgumentTypeError(msg)

        config_dict = getattr(namespace, self.dest)
        if not config_dict:
            config_dict = dict()
            setattr(namespace, self.dest, config_dict)

        val = self._cast_value(m.group(2))
        set_config_value(config_dict, val, *m.group(1).split('.'))

class BooleanConfigOptionAction(ConfigOptionAction):
    TRUE_VALS = set(['true', "1"])
    FALSE_VALS = set(['false', "0"])
    def _cast_value(self, val):
        val = val.lower()
        if val in self.TRUE_VALS:
            return True
        elif val in self.FALSE_VALS:
            return False
        else:
            raise ArgumentTypeError(
                "Invalid boolean value: {}".format(val))

class IntegerConfigOptionAction(ConfigOptionAction):
    def _cast_value(self, val):
        try:
            return int(val)
        except ValueError:
            raise ArgumentTypeError(
                "Invalid integer value: {}".format(val))

class FloatConfigOptionAction(ConfigOptionAction):
    def _cast_value(self, val):
        try:
            return float(val)
        except ValueError:
            raise ArgumentTypeError(
                "Invalid float value: {}".format(val))

class JSONConfigOptionAction(ConfigOptionAction):
    def _cast_value(self, val):
        try:
            return json.loads(val)
        except ValueError:
            raise ArgumentTypeError(
                "Invalid json value: {}".format(val))

class ConfigFileAction(Action):
    def __call__(self, parser, namespace, value, option_string=None):
        """Load config settings from json file
        """
        filename = os.path.abspath(value.strip())
        if not os.path.isfile(filename):
            raise ArgumentTypeError(
                "File {} does not exist".format(filename))

        with open(filename) as f:
            try:
                config_dict = json.loads(f.read())
            except ValueError:
                raise ArgumentTypeError("File {} contains "
                    "invalid config JSON data".format(filename))

        if 'config' not in config_dict:
            raise ArgumentTypeError("Config file must contain top "
                "level 'config' key")
        config_dict = config_dict['config']

        existing_config_dict = getattr(namespace, self.dest)
        if not existing_config_dict:
            # first file loaded
            setattr(namespace, self.dest, config_dict)
        else:
            # subsequent file loaded
            merge_configs(existing_config_dict, config_dict)

class LogLevelAction(Action):

    LOG_LEVELS = [
        'DEBUG',
        'INFO',
        'WARNING',
        'ERROR',
        'CRITICAL'
    ]

    def __call__(self, parser, namespace, value, option_string=None):
        """Parses log level string ('DEBUG', 'INFO', etc.)
        """
        if value:
            log_level = value.strip().upper()
            if log_level not in self.LOG_LEVELS:
                raise ArgumentTypeError('Invalid log level: %s' % (log_level))
            level = getattr(logging, log_level)
            setattr(namespace, self.dest, level)


##
## Helper Methods
##

## Argument Parsing

def add_arguments(parser, argument_hashes, required=False):
    for o in argument_hashes:
        opt_strs = [e for e in [o.get('short'), o.get('long')] if e]
        kwargs = dict([(k,v) for k,v in o.items() if k not in ('short', 'long')])
        if required:
            kwargs.update(required=True)
        parser.add_argument(*opt_strs, **kwargs)

def output_args(args):
    for k,v in args.__dict__.items():
        logging.info("%s: %s" % (' '.join(k.split('_')), v))

## Configuration related options

CONFIGURATION_OPTIONS = [
    {
        'short': "-C",
        'long': '--config-option',
        'dest': 'config_options',
        'help': "Config option override, formatted like 'section.*.key=stringvalue'",
        'action': ConfigOptionAction
    },
    {
        'short': "-B",
        'long': '--boolean-config-option',
        'dest': 'config_options',
        'help': "Config option override, formatted like 'section.*.key=boolvalue'",
        'action': BooleanConfigOptionAction
    },
    {
        'short': "-I",
        'long': '--integer-config-option',
        'dest': 'config_options',
        'help': "Config option override, formatted like 'section.*.key=intvalue'",
        'action': IntegerConfigOptionAction
    },
    {
        'short': "-F",
        'long': '--float-config-option',
        'dest': 'config_options',
        'help': "Config option override, formatted like 'section.*.key=floatvalue'",
        'action': FloatConfigOptionAction
    },
    {
        'short': "-J",
        'long': '--json-config-option',
        'dest': 'config_options',
        'help': "Config option override supporting any json formatted value, formatted like 'section.*.key=jsonvalue'",
        'action': JSONConfigOptionAction
    },
    {
        'short': '-c',
        'long': '--config-file',
        'dest': 'config_file_options',
        'help': 'config file comtaining JSON formatted overrides for default config values',
        'action': ConfigFileAction
    }
]

def add_configuration_options(parser, support_short_names=False):
    options = copy.copy(CONFIGURATION_OPTIONS)
    if not support_short_names:
        for o in options:
            o.pop('short')
    add_arguments(parser, options)

## Logging Related Options

def add_logging_options(parser):
    add_arguments(parser, [
        {
            'long': "--log-level",
            'dest': "log_level",
            'action': LogLevelAction,
            'default': logging.WARNING,
            'help': "python log level (%s); default WARNING" % (
                ','.join(LogLevelAction.LOG_LEVELS))
        },
        {
            'long': "--log-file",
            'dest': "log_file",
            'action': "store",
            'default': None,
            'help': "log file"
        },
        {
            'long': "--log-message-format",
            'dest': "log_message_format",
            'action': "store",
            'default': None,
            'help': "log message format"
        },
    ])

def configure_logging_from_args(args, parser):
    log_message_format = args.log_message_format or '%(asctime)s %(levelname)s: %(message)s'

    logging.basicConfig(format=log_message_format, level=args.log_level,
        filename=args.log_file)
