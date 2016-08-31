__author__      = "Joel Dubowy"

import logging
import sys

__all__ = [
    'exit_with_msg',
    'log_config'
]

def exit_with_msg(msg, extra_output=None, output=None, exit_code=1,
        prefix="*** ERROR: ", extra_preceeding_output=None):
    """Prints message and exits
    """
    output = output or sys.stderr.write
    if extra_preceeding_output:
        extra_preceeding_output()
    output("\n%s%s\n" % (prefix, msg))
    if extra_output:
        output('\n')
        extra_output()
    output('\n')
    sys.exit(exit_code)

def log_config(config, log_method=None):
    if not config:
        return

    log_method = log_method or logging.info

    log_method('Config Settings:')

    for option, val in config.defaults().items():
        log_method(" *   [DEFAULT] %s = %s" % (option.upper(), val))

    for section in config.sections():
        for option in config.options(section):
            val = config.get(section, option)
            log_method(" *   [%s] %s = %s" % (section, option.upper(), val))
