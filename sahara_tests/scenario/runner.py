#!/usr/bin/env python

# Copyright (c) 2015 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
import argparse
import collections
import os
import shutil
import subprocess
import sys
import tempfile

from oslo_utils import fileutils
import os_client_config
import pkg_resources as pkg
import six
import yaml

from sahara_tests.scenario import utils
from sahara_tests.scenario import validation
from sahara_tests import version


def set_defaults(config):
    # set up credentials
    config['credentials'] = config.get('credentials', {})
    creds = config['credentials']
    creds.setdefault('sahara_service_type', 'data-processing')
    creds['sahara_url'] = creds.get('sahara_url', None)
    creds['ssl_verify'] = creds.get('ssl_verify', False)
    creds['ssl_cert'] = creds.get('ssl_cert', None)

    # set up network
    config['network'] = config.get('network', {})
    net = config['network']
    net['type'] = net.get('type', 'neutron')
    net['private_network'] = net.get('private_network', 'private')
    net['auto_assignment_floating_ip'] = net.get('auto_assignment_floating_ip',
                                                 False)
    net['public_network'] = net.get('public_network', '')

    default_scenario = ['run_jobs', 'scale', 'run_jobs']

    # set up tests parameters
    for testcase in config['clusters']:
        testcase['class_name'] = "".join([
            testcase['plugin_name'],
            testcase['plugin_version'].replace('.', '_')])
        testcase['retain_resources'] = testcase.get('retain_resources', False)
        testcase['scenario'] = testcase.get('scenario', default_scenario)
        if isinstance(testcase.get('edp_jobs_flow'), six.string_types):
            testcase['edp_jobs_flow'] = [testcase['edp_jobs_flow']]
        edp_jobs_flow = []
        for edp_flow in testcase.get('edp_jobs_flow', []):
            edp_jobs_flow.extend(config.get('edp_jobs_flow',
                                            {}).get(edp_flow))
        testcase['edp_jobs_flow'] = edp_jobs_flow


def recursive_walk(directory):
    list_of_files = []
    for file in os.listdir(directory):
        path = os.path.join(directory, file)
        if os.path.isfile(path):
            list_of_files.append(path)
        else:
            list_of_files += recursive_walk(path)
    return list_of_files


def valid_count(value):
    try:
        ivalue = int(value)
        if ivalue <= 0:
            raise ValueError
    except ValueError:
        raise argparse.ArgumentTypeError("%s is an invalid value of count. "
                                         "Value must be int and > 0. " % value)
    return ivalue


def parse_args(array):
    args = collections.OrderedDict()
    for pair in array:
        arg_dict = pair.split(':')
        if len(arg_dict) < 2:
            return args
        args[arg_dict[0]] = "\'%s\'" % arg_dict[1]
    return args


def get_base_parser():
    parser = argparse.ArgumentParser(description="Scenario tests runner.")

    parser.add_argument('scenario_arguments', help="Path to scenario files",
                        nargs='*', default=[])
    parser.add_argument('--variable_file', '-V', default='', nargs='?',
                        help='Path to the file with template variables')
    parser.add_argument('--verbose', default=False, action='store_true',
                        help='Increase output verbosity')
    parser.add_argument('--validate', default=False, action='store_true',
                        help='Validate yaml-files, tests will not be runned')
    parser.add_argument('--args', default='', nargs='+',
                        help='Pairs of arguments key:value')
    parser.add_argument('--plugin', '-p', default=None, nargs='?',
                        help='Specify plugin name')
    parser.add_argument('--plugin_version', '-v', default=None,
                        nargs='?', help='Specify plugin version')
    parser.add_argument('--release', '-r', default=None,
                        nargs='?', help='Specify Sahara release')
    parser.add_argument('--report', default=False, action='store_true',
                        help='Write results of test to file')
    parser.add_argument('--feature', '-f', default=[],
                        action='append', help='Set of features to enable')
    parser.add_argument('--count', default=1, nargs='?', type=valid_count,
                        help='Specify count of runs current cases.')
    parser.add_argument('--v2', '-2', default=False, action='store_true',
                        help='Use APIv2')
    return parser


def get_scenario_files(scenario_arguments):
    files = []
    for scenario_argument in scenario_arguments:
        if os.path.isdir(scenario_argument):
            files += recursive_walk(scenario_argument)
        if os.path.isfile(scenario_argument):
            files.append(scenario_argument)

    return files


def main():
    # parse args
    cloud_config = os_client_config.OpenStackConfig()
    parser = get_base_parser()
    cloud_config.register_argparse_arguments(parser, sys.argv)
    args = parser.parse_args()

    scenario_arguments = args.scenario_arguments
    variable_file = args.variable_file
    verbose_run = args.verbose
    scenario_args = parse_args(args.args)
    plugin = args.plugin
    version = args.plugin_version
    release = args.release
    report = args.report
    features = args.feature
    count = args.count
    use_api_v2 = args.v2

    auth_values = utils.get_auth_values(cloud_config, args)

    scenario_arguments = utils.get_default_templates(plugin, version, release,
                                                     scenario_arguments,
                                                     features)

    files = get_scenario_files(scenario_arguments)

    template_variables = utils.get_templates_variables(files, variable_file,
                                                       verbose_run,
                                                       scenario_args,
                                                       auth_values)

    params_for_login = {'credentials': auth_values}
    config = utils.generate_config(files, template_variables, params_for_login,
                                   verbose_run, features)

    # validate config
    validation.validate(config)

    if args.validate:
        return

    set_defaults(config)
    credentials = config['credentials']
    network = config['network']
    testcases = config['clusters']
    for case in range(count - 1):
        testcases.extend(config['clusters'])

    test_dir_path = utils.create_testcase_file(testcases, credentials, network,
                                               report, use_api_v2=use_api_v2)

    # run tests
    concurrency = config.get('concurrency')
    testr_runner_exit_code = utils.run_tests(concurrency, test_dir_path)
    sys.exit(testr_runner_exit_code)

if __name__ == '__main__':
    main()
