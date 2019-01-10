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

from mako import template as mako_template
from oslo_utils import fileutils
from oslo_utils import uuidutils
import os_client_config
import pkg_resources as pkg
import six
import yaml

from sahara_tests.scenario import validation
from sahara_tests import version


SCENARIO_RESOURCES_DIR = pkg.resource_filename(version.version_info.package,
                                               'scenario')

TEST_TEMPLATE_DIR = os.path.join(SCENARIO_RESOURCES_DIR, 'defaults/')
DEFAULT_TEMPLATE_VARS = [os.path.join(TEST_TEMPLATE_DIR,
                                      'credentials.yaml.mako'),
                         os.path.join(TEST_TEMPLATE_DIR,
                                      'edp.yaml.mako')]
TEST_TEMPLATE_PATH = os.path.join(SCENARIO_RESOURCES_DIR,
                                  'testcase.py.mako')
DEFAULT_STESTR_CONF = os.path.join(SCENARIO_RESOURCES_DIR, 'stestr.conf')


def rand_name(name=''):
    rand_data = uuidutils.generate_uuid()[:8]
    if name:
        return '%s-%s' % (name, rand_data)
    else:
        return rand_data


def run_tests(concurrency, test_dir_path):
    command = ['stestr', 'run']
    if concurrency:
        command.extend(['--concurrency=%d' % concurrency])
    new_env = os.environ.copy()
    tester_runner = subprocess.Popen(command, env=new_env, cwd=test_dir_path)
    tester_runner.communicate()
    return tester_runner.returncode


def create_testcase_file(testcases, credentials, network, report,
                         use_api_v2=False):
    # current directory, where to write reports, key files, etc, if required
    results_dir = os.getcwd()
    default_templ_dir = os.path.abspath(TEST_TEMPLATE_DIR)

    # create testcase file
    test_template = mako_template.Template(filename=TEST_TEMPLATE_PATH)
    testcase_data = test_template.render(testcases=testcases,
                                         credentials=credentials,
                                         network=network, report=report,
                                         results_dir=results_dir,
                                         default_templ_dir=default_templ_dir,
                                         use_api_v2=use_api_v2)

    test_dir_path = tempfile.mkdtemp()
    print("The generated test file located at: %s" % test_dir_path)
    fileutils.write_to_tempfile(testcase_data.encode("ASCII"), prefix='test_',
                                suffix='.py', path=test_dir_path)
    # Copy both files as long as the old runner is supported
    shutil.copyfile(DEFAULT_STESTR_CONF, os.path.join(test_dir_path,
                                                      '.stestr.conf'))

    return test_dir_path


def get_templates_variables(files, variable_file, verbose_run, scenario_args,
                            auth_values):
    template_variables = {}
    if any(is_template_file(config_file) for config_file in files):
        template_variables = read_template_variables(variable_file,
                                                     verbose_run,
                                                     scenario_args)
    template_variables.update(read_template_variables(
        verbose=verbose_run, scenario_args=scenario_args,
        auth_values=auth_values))
    return template_variables


def generate_config(files, template_variables, auth_values, verbose_run,
                    features_list=None):
    config = {'credentials': {},
              'network': {},
              'clusters': [],
              'edp_jobs_flow': {}}

    for scenario_argument in files:
        test_scenario = read_scenario_config(scenario_argument,
                                             template_variables, verbose_run)
        config = _merge_dicts_sections(test_scenario, config, 'credentials')
        config = _merge_dicts_sections(test_scenario, config, 'network')

        if test_scenario.get('clusters') is not None:
            config['clusters'] += test_scenario['clusters']

        if test_scenario.get('edp_jobs_flow') is not None:
            for key in test_scenario['edp_jobs_flow']:
                if key not in config['edp_jobs_flow']:
                    config['edp_jobs_flow'][key] = (
                        test_scenario['edp_jobs_flow'][key])
                else:
                    raise ValueError('Job flow exist')
    config['credentials'].update(auth_values['credentials'])

    # filter out the jobs depending on the features, if any
    unknown_jobs = []
    if features_list is None:
        features_list = []
    for cluster in config['clusters']:
        if cluster.get('edp_jobs_flow'):
            filtered_jobs = []
            # The jobs associated to a cluster may be a single value (string)
            # or a list of values; handle both cases.
            cluster_jobs_list = cluster['edp_jobs_flow']
            if isinstance(cluster_jobs_list, six.string_types):
                cluster_jobs_list = [cluster_jobs_list]
            for job_item in cluster_jobs_list:
                if isinstance(job_item, dict):
                    job = job_item['name']
                else:
                    job = job_item

                # get the list of features, if defined
                job_features = set()
                if isinstance(job_item, dict):
                    job_features = set(job_item.get('features', []))
                # If a job has no features associated, it is always used.
                # Otherwise, it should be used only if any of its features
                # matches any of the features requested,
                if (not job_features or
                    (features_list is not None and
                     job_features.intersection(features_list))):
                    # the job is relevant for the configuration,
                    # so it must be defined; if it is not, it will break,
                    # so take note of the name
                    if job not in config['edp_jobs_flow']:
                        unknown_jobs.append(job)
                        continue
                    # job defined, it can be used
                    filtered_jobs.append(job)

            cluster['edp_jobs_flow'] = filtered_jobs
    if unknown_jobs:
        # Some jobs which are listed in some clusters
        # are not defined, stop here
        raise ValueError('Unknown jobs: %s' % (unknown_jobs))

    if verbose_run:
        six.print_("Generated configuration:\n%s" % (
            yaml.safe_dump(config,
                           allow_unicode=True,
                           default_flow_style=False)),
                   flush=True)
    return config


def get_default_templates(plugin, version, release, scenario_arguments,
                          features=None):
    all_templates = []

    templates_location = TEST_TEMPLATE_DIR
    if release is not None:
        templates_location = os.path.join(TEST_TEMPLATE_DIR, release)

    if plugin:
        if plugin in ['transient', 'fake']:
            template = "%s.yaml.mako" % plugin
        elif plugin and version:
            template = "%s-%s.yaml.mako" % (plugin, version)
        else:
            raise ValueError("Please, specify version for plugin via '-v'")

        # find the templates for each features, if they exist
        feature_templates_vars = []
        if features:
            default_templates_base = []
            for default_template in DEFAULT_TEMPLATE_VARS:
                if default_template.endswith('.yaml.mako'):
                    default_templates_base.append(
                        default_template[:-len('.yaml.mako')])
            # for each default template, look for a corresponding
            # <file>_<feature>.yaml.mako
            for feature in features:
                for default_template_base in default_templates_base:
                    template_feature = '%s_%s.yaml.mako' % (
                        default_template_base, feature)
                    if os.path.exists(template_feature):
                        feature_templates_vars.append(template_feature)

        # return a combination of: default templates, version-specific
        # templates, feature-based templates
        all_templates = DEFAULT_TEMPLATE_VARS + [os.path.join(
            templates_location, template)] + feature_templates_vars

    # it makes sense that all the other templates passed as arguments
    # are always added at the end
    all_templates += scenario_arguments
    return all_templates


def get_auth_values(cloud_config, args):
    try:
        cloud = cloud_config.get_one_cloud(argparse=args)
        cloud_credentials = cloud.get_auth_args()
        api_version = cloud.config.get('identity_api_version')
    except os_client_config.exceptions.OpenStackConfigException:
        # cloud not found
        api_version = '2.0'
        cloud_credentials = {}
    auth_values = {
        'os_username': cloud_credentials.get('username', 'admin'),
        'os_password': cloud_credentials.get('password', 'nova'),
        'os_auth_url': cloud_credentials.get('auth_url',
                                             'http://localhost:5000/v2.0'),
        'os_tenant': cloud_credentials.get('project_name', 'admin')
    }
    auth_url = auth_values['os_auth_url']
    if not any(v in auth_url for v in ('v2.0', 'v3')):
        version = 'v3' if api_version in ('3', '3.0') else 'v2.0'
        auth_values['os_auth_url'] = "%s/%s" % (auth_url, version)
    return auth_values


def _merge_dicts_sections(dict_with_section, dict_for_merge, section):
    if dict_with_section.get(section) is not None:
        for key in dict_with_section[section]:
            if dict_for_merge[section].get(key) is not None:
                if dict_for_merge[section][key] != (
                        dict_with_section[section][key]):
                    raise ValueError('Sections %s is different' % section)
            else:
                dict_for_merge[section][key] = dict_with_section[section][key]
    return dict_for_merge


def is_template_file(config_file):
    return config_file.endswith(('.yaml.mako', '.yml.mako'))


def read_template_variables(variable_file=None, verbose=False,
                            scenario_args=None, auth_values=None):
    variables = {}
    try:
        cp = six.moves.configparser.ConfigParser()
        # key-sensitive keys
        if variable_file:
            cp.optionxform = lambda option: option
            cp.readfp(open(variable_file))
        variables = cp.defaults()
        if scenario_args:
            variables.update(scenario_args)
        if auth_values:
            variables.update(auth_values)
    except IOError as ioe:
        print("WARNING: the input contains at least one template, but "
              "the variable configuration file '%s' is not valid: %s" %
              (variable_file, ioe))
    except six.moves.configparser.Error as cpe:
        print("WARNING: the input contains at least one template, but "
              "the variable configuration file '%s' can not be parsed: "
              "%s" % (variable_file, cpe))
    finally:
        if verbose:
            six.print_("Template variables:\n%s" % (variables), flush=True)
    # continue anyway, as the templates could require no variables
    return variables


def read_scenario_config(scenario_config, template_vars=None,
                         verbose=False):
    """Parse the YAML or the YAML template file.

    If the file is a YAML template file, expand it first.
    """

    yaml_file = ''
    if is_template_file(scenario_config):
        scenario_template = mako_template.Template(filename=scenario_config,
                                                   strict_undefined=True)
        template = scenario_template.render_unicode(**template_vars)
        yaml_file = yaml.safe_load(template)
    else:
        with open(scenario_config, 'r') as yaml_file:
            yaml_file = yaml.safe_load(yaml_file)
    if verbose:
        six.print_("YAML from %s:\n%s" % (scenario_config,
                                          yaml.safe_dump(
                                              yaml_file,
                                              allow_unicode=True,
                                              default_flow_style=False)),
                   flush=True)
    return yaml_file
