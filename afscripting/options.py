__author__      = "Joel Dubowy"

import datetime
import logging
import re
import warnings
from optparse import OptionValueError, OptionParser

from afdatetime.parsing import parse as _parse_datetime

from .utils import exit_with_msg

__all__ = [
    'add_options',
    'parse_options',
    'check_required_options',
    'output_options',
    'extract_and_set_key_value',
    'parse_datetime',
    'append_or_split_with_delimiter_and_extend',
    'append_or_split_and_extend',
    'add_logging_options',
    'configure_logging_from_options'
]

def add_options(parser, option_hashes):
    for o in option_hashes:
        opt_strs = [e for e in [o.get('short'), o.get('long')] if e]
        kwargs = dict([(k,v) for k,v in o.items() if k not in ('short', 'long')])
        parser.add_option(*opt_strs, **kwargs)

def parse_options(required_options, optional_options,
        usage="usage: %prog [options]", pre_validation=None,
        post_options_outputter=None):
    """....

    Arguments:
     - required_options --
     - optional_options --
    Kwargs
     - usage --
     - pre_validation --
     - extra_help_output -- callable that generates text to be output after
        options are listed
    """
    warnings.warn("Deprecated - use pyairfire.scripting.args.parse_args", DeprecationWarning)
    # Parse options
    parser = OptionParser(usage=usage)
    if post_options_outputter:
        parser.format_epilog = lambda formatter: post_options_outputter()
    add_options(parser, required_options)
    add_options(parser, optional_options)
    add_logging_options(parser)
    options, args = parser.parse_args()
    # Configure logging
    configure_logging_from_options(options, parser)
    # Do any pre-validation logic
    if pre_validation:
        pre_validation(parser, options)
    # Check options
    check_required_options(options, required_options, parser)
    # Output options
    output_options(options)

    return parser, options, args

def check_required_options(options, required_options, parser):
    """Checks that all required options are defined

    Arguments:
     - options --
     - required_options -- array of required option tuples (see note below)
     - parser -- optparse.OptionParser instance

    Expects required options to be of the form:

        REQUIRED_OPTIONS = [
            {
                'short': '-f',
                'long': '--foo-bar',
                'dest': 'foo_bar',
                'help': 'foo bar help (required)'
            },

            ...
        ]

    where the last element of each tuple is the attribute name in the options object.
    """
    for o in required_options:
        dest = o.get('dest') or '_'.join((o.get('long') or o.get('short')).strip('-').split('-'))
        if not options.__dict__[dest]:
            opt_strs = "'/'".join([e for e in [o.get('short'), o.get('long')] if e])
            msg = "specify '%s'" % (opt_strs)
            exit_with_msg(msg, parser.print_help())

def output_options(options):
    for k,v in options.__dict__.items():
        logging.info("%s: %s" % (' '.join(k.split('_')), v))

## Callbacks for add_option

KEY_VALUE_EXTRACTER = re.compile('^([^=]+)=([^=]+)$')

def extract_and_set_key_value(option, opt, value, parser):
    """Splits value into key/value, and set in destination dict

    Note: Expects value to be of the format 'key=value'.  Also expects
    destination (i.e. parser.values's option.dest attribute), to be
    initialized as an empty dict.
    """
    m = KEY_VALUE_EXTRACTER.search(value.strip())
    if not m:
        msg = "Invalid value '%s' for option '%s' - values must be of the form 'key=value'" % (
            value, opt)
        raise OptionValueError(msg)
    d = getattr(parser.values, option.dest)
    d[m.group(1)] = m.group(2)

def parse_datetime(option, opt, value, parser):
    """Parses datetime from string value

    Note: Expects value to be of one of the formats listed in
    afdatetime.parsing.RECOGNIZED_DATETIME_FORMATS
    """
    try:
        dt = _parse_datetime(value)
    except ValueError:
        # If we got here, none of them matched, so raise error
        raise OptionValueError("Invalid datetime format '%s' for option %s" % (
            value, opt))
    setattr(parser.values, option.dest, dt)


def append_or_split_with_delimiter_and_extend(dilimiter):
    """Generates a callback function that augments the append action with the
    ability to split a string and extend the redsulting values to the option array

    Args:
     - delimiter -- character used to to split the string string
    """
    def c(option, opt, value, parser):
        d = getattr(parser.values, option.dest)
        d.extend(value.split(dilimiter))
    return c
append_or_split_and_extend = append_or_split_with_delimiter_and_extend(',')
"""For convenience, returns callback generated by
append_or_split_with_delimiter_and_extend with comma as the dilimiter
"""

# Logging Related Options

LOG_LEVELS = [
    'DEBUG',
    'INFO',
    'WARNING',
    'ERROR',
    'CRITICAL'
]

def add_logging_options(parser):
    add_options(parser, [
        {
            'long': "--log-level",
            'dest': "log_level",
            'action': "store",
            'default': None,
            'help': "python log level (%s)" % (','.join(LOG_LEVELS))
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

def configure_logging_from_options(options, parser):
    level = logging.WARNING  # default
    if options.log_level:
        log_level = options.log_level.upper()
        if log_level not in LOG_LEVELS:
            exit_with_msg(
                'Invalid log level: %s' % (log_level))
        level = getattr(logging, log_level)

    log_message_format = options.log_message_format or '%(asctime)s %(levelname)s: %(message)s'

    logging.basicConfig(format=log_message_format, level=level, filename=options.log_file)
