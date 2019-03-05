'''Unit tests for afscripting.args'''

__author__ = "Joel Dubowy"

import argparse
import tempfile

from py.test import raises

import afscripting

##
## Tests for Fire
##

def parse_args(args, options):
    parser = argparse.ArgumentParser()
    for o in options:
        parser.add_argument(*o["flags"], **o["kwargs"])
    # ...Create your parser as you like...
    return parser.parse_args(args)

class TestCreateConfigFileAction(object):

    def add_option_and_parse(self, filenames, keys=None):
        args = []
        for f in filenames:
            args.extend(["-c", f])

        action = (afscripting.args.create_config_file_action(keys)
            if keys else afscripting.args.ConfigFileAction)

        options = [{
            "flags": ['-c', '--config-file'],
            "kwargs": {
                'dest': 'config_file_options',
                'action': action
            }
        }]

        return parse_args(args, options)

    def test_invalid_json(self):
        with tempfile.NamedTemporaryFile('w+t') as f:
            f.write('''{
                "config": {
                    "Foo": wer
                }
            }''')
            f.flush()
            with raises(argparse.ArgumentTypeError) as e:
                p = self.add_option_and_parse([f.name])

    def test_default(self):
        with tempfile.NamedTemporaryFile('w+t') as f:
            f.write('''{
                "config": {
                    "Foo": "bar"
                },
                "ignored": {
                    "SDF": 1123
                }
            }''')
            f.flush()
            p = self.add_option_and_parse([f.name])
            assert p.config_file_options == {
                "Foo": "bar"
            }

    def test_altername_keys_both_defined(self):
        with tempfile.NamedTemporaryFile('w+t') as f:
            # takes whichever key occurs first in list
            f.write('''{
                "config": {
                    "Foo": "bar"
                },
                "ignored": {
                    "SDF": 1123
                },
                "run_config": {
                    "bar": "sdfsdfsdf"
                }
            }''')
            f.flush()
            p = self.add_option_and_parse([f.name],
                keys=["config", "run_config"])
            assert p.config_file_options == {"Foo": "bar"}
            p = self.add_option_and_parse([f.name],
                keys=["run_config", "config"])
            assert p.config_file_options == {"bar": "sdfsdfsdf"}

    def test_altername_keys_one_defined(self):
        with tempfile.NamedTemporaryFile('w+t') as f:
            # takes whichever key occurs first in list
            f.write('''{
                "config": {
                    "Foo": "bar"
                },
                "ignored": {
                    "SDF": 1123
                }
            }''')
            f.flush()
            p = self.add_option_and_parse([f.name],
                keys=["run_config", "config"])
            assert p.config_file_options == {"Foo": "bar"}
            p = self.add_option_and_parse([f.name],
                keys=["config", "run_config"])
            assert p.config_file_options == {"Foo": "bar"}


    def test_multiple_files(self):
        with tempfile.NamedTemporaryFile('w+t') as f1:
            with tempfile.NamedTemporaryFile('w+t') as f2:
                f1.write('''{
                    "config": {
                        "Foo": "bar",
                        "bar": "Baz"
                    }
                }''')
                f1.flush()
                f2.write('''{
                    "config": {
                        "bar": "sdfsdf",
                        "baz": 123123
                    }
                }''')
                f2.flush()
                p = self.add_option_and_parse([f1.name, f2.name])
                assert p.config_file_options == {
                    "Foo": "bar",
                    "bar": "sdfsdf",
                    "baz": 123123
                }
