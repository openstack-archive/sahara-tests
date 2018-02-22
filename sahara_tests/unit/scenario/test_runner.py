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

import os
import sys

from jsonschema import exceptions
import pkg_resources as pkg
import mock
import testtools

from sahara_tests import version
from sahara_tests.scenario import runner


def _create_subprocess_communicate_mock():
    communicate_mock = mock.Mock()
    communicate_mock.communicate.return_value = ["", ""]
    return communicate_mock


class RunnerUnitTest(testtools.TestCase):

    def _isDictContainSubset(self, sub_dictionary, dictionary):
        for key in sub_dictionary:
            if sub_dictionary[key] != dictionary[key]:
                return False
        return True

    def test_set_defaults(self):
        config_without_cred_net = {
            "clusters": [
                {
                    "plugin_name": "vanilla",
                    "plugin_version": "2.7.1",
                    "image": "sahara-vanilla-2.7.1-ubuntu-14.04"
                }
            ]
        }

        expected_default_credential = {
            "credentials": {
                "sahara_url": None,
                "sahara_service_type": "data-processing",
                "ssl_cert": None,
                "ssl_verify": False
            }
        }

        expected_default_network = {
            "network": {
                "type": "neutron",
                "private_network": "private",
                "public_network": "",
                "auto_assignment_floating_ip": False
            }
        }

        expected_default_cluster = {
            "clusters": [
                {
                    "image": "sahara-vanilla-2.7.1-ubuntu-14.04",
                    "edp_jobs_flow": [],
                    "class_name": "vanilla2_7_1",
                    "plugin_name": "vanilla",
                    "scenario": ['run_jobs', 'scale', 'run_jobs'],
                    "plugin_version": "2.7.1",
                    "retain_resources": False,
                }
            ]
        }

        runner.set_defaults(config_without_cred_net)

        self.assertTrue(self._isDictContainSubset(
            expected_default_credential, config_without_cred_net))
        self.assertTrue(self._isDictContainSubset(
            expected_default_network, config_without_cred_net))
        self.assertTrue(self._isDictContainSubset(
            expected_default_cluster, config_without_cred_net))

        config = {
            "credentials": {
                "os_username": "changed_admin",
                "os_auth_url": "http://127.0.0.1:5000/v2.0",
                "sahara_url": "http://127.0.0.1",
                "os_password": "changed_nova",
                "os_tenant": "changed_admin",
                "ssl_cert": "sahara_tests/unit/scenario/dummy.crt"
            },
            "network": {
                "type": "neutron",
                "private_network": "changed_private",
                "public_network": "changed_public",
                "auto_assignment_floating_ip": True,
            },
            "clusters": [
                {
                    "plugin_name": "vanilla",
                    "plugin_version": "2.7.1",
                    "image": "sahara-vanilla-2.7.1-ubuntu-14.04",
                    "edp_jobs_flow": "test_flow",
                    "retain_resources": True
                }
            ],
            "edp_jobs_flow": {
                "test_flow": [
                    {
                        "type": "Pig",
                        "input_datasource": {
                            "type": "swift",
                            "source": "sahara_tests/scenario/defaults/"
                                      "edp-examples/edp-pig/top-todoers/"
                                      "data/input"
                        },
                        "output_datasource": {
                            "type": "hdfs",
                            "destination": "/user/hadoop/edp-output"
                        },
                        "main_lib": {
                            "type": "swift",
                            "source": "sahara_tests/scenario/defaults/"
                                      "edp-examples/edp-pig/top-todoers/"
                                      "example.pig"
                        }
                    },
                    {
                        "type": "Java",
                        "additional_libs": [
                            {
                                "type": "database",
                                "source": 'sahara_tests/scenario/defaults/'
                                          'edp-examples/hadoop2/edp-java/'
                                          'hadoop-mapreduce-examples-'
                                          '2.6.0.jars',
                            }],
                        "configs": "edp.java.main_class: org.apache.hadoop."
                                   "examples.QuasiMonteCarlo",
                        "args": [10, 10]
                    },
                ],
                "test_flow2": [
                    {
                        "type": "Java",
                        "additional_libs": [
                            {
                                "type": "database",
                                "source":
                                    "sahara_tests/scenario/defaults/"
                                    "edp-examples/hadoop2/edp-java/hadoop-"
                                    "mapreduce-examples-2.6.0.jars"
                            }],
                        "configs": "edp.java.main_class: org.apache.hadoop."
                                   "examples.QuasiMonteCarlo",
                        "args": [20, 20]
                    }
                ]
            }
        }

        expected_credential = {
            "credentials": {
                "os_username": "changed_admin",
                "os_auth_url": "http://127.0.0.1:5000/v2.0",
                "sahara_url": "http://127.0.0.1",
                "os_password": "changed_nova",
                "os_tenant": "changed_admin",
                "sahara_service_type": "data-processing",
                "ssl_cert": "sahara_tests/unit/scenario/dummy.crt",
                "ssl_verify": False
            },
        }

        expected_network = {
            "network": {
                "type": "neutron",
                "private_network": "changed_private",
                "public_network": "changed_public",
                "auto_assignment_floating_ip": True,
            }
        }

        expected_cluster = {
            "clusters": [
                {
                    "plugin_name": "vanilla",
                    "plugin_version": "2.7.1",
                    "image": "sahara-vanilla-2.7.1-ubuntu-14.04",
                    "retain_resources": True,
                    'edp_jobs_flow': [
                        {
                            'main_lib': {
                                'source': 'sahara_tests/scenario/defaults/'
                                          'edp-examples/edp-pig/'
                                          'top-todoers/example.pig',
                                'type': 'swift'
                            },
                            'type': 'Pig',
                            'input_datasource': {
                                'source': 'sahara_tests/scenario/defaults/'
                                          'edp-examples/edp-pig/'
                                          'top-todoers/data/input',
                                'type': 'swift'
                            },
                            'output_datasource': {
                                'type': 'hdfs',
                                'destination': '/user/hadoop/edp-output'
                            }
                        },
                        {
                            'args': [10, 10],
                            'configs': 'edp.java.main_class: org.apache.'
                                       'hadoop.examples.QuasiMonteCarlo',
                            'type': 'Java',
                            'additional_libs': [
                                {
                                    'source': 'sahara_tests/scenario/defaults/'
                                              'edp-examples/hadoop2/edp-java/'
                                              'hadoop-mapreduce-examples-'
                                              '2.6.0.jars',
                                    'type': 'database'
                                }]
                        }
                    ],
                    "scenario": ['run_jobs', 'scale', 'run_jobs'],
                    "class_name": "vanilla2_7_1"
                }],
        }

        runner.set_defaults(config)

        self.assertTrue(self._isDictContainSubset(
            expected_credential, config))
        self.assertTrue(self._isDictContainSubset(
            expected_network, config))
        self.assertTrue(self._isDictContainSubset(
            expected_cluster, config))

    @mock.patch('sys.exit', return_value=None)
    @mock.patch('subprocess.Popen',
                return_value=_create_subprocess_communicate_mock())
    def test_runner_main(self, mock_sub, mock_sys):
        sys.argv = ['sahara_tests/scenario/runner.py',
                    'sahara_tests/unit/scenario/vanilla2_7_1.yaml']
        runner.main()

    @mock.patch('sys.exit', return_value=None)
    @mock.patch('subprocess.Popen',
                return_value=_create_subprocess_communicate_mock())
    def test_runner_template_missing_varfile(self, mock_sub, mock_sys):
        sys.argv = ['sahara_tests/scenario/runner.py',
                    'sahara_tests/unit/scenario/vanilla2_7_1.yaml.mako']
        self.assertRaises(NameError, runner.main)

    @mock.patch('sys.exit', return_value=None)
    @mock.patch('subprocess.Popen',
                return_value=_create_subprocess_communicate_mock())
    def test_runner_template_wrong_varfile(self, mock_sub, mock_sys):
        sys.argv = ['sahara_tests/scenario/runner.py',
                    '-V',
                    'sahara_tests/unit/scenario/templatevars_nodefault.ini',
                    'sahara_tests/unit/scenario/vanilla2_7_1.yaml.mako']
        self.assertRaises(NameError, runner.main)

    @mock.patch('sys.exit', return_value=None)
    @mock.patch('subprocess.Popen',
                return_value=_create_subprocess_communicate_mock())
    def test_runner_template_incomplete_varfile(self, mock_sub, mock_sys):
        sys.argv = ['sahara_tests/scenario/runner.py',
                    '-V',
                    'sahara_tests/unit/scenario/templatevars_incomplete.ini',
                    'sahara_tests/unit/scenario/vanilla2_7_1.yaml.mako']
        self.assertRaises(NameError, runner.main)

    @mock.patch('sys.exit', return_value=None)
    @mock.patch('subprocess.Popen',
                return_value=_create_subprocess_communicate_mock())
    def test_runner_template_working(self, mock_sub, mock_sys):
        sys.argv = ['sahara_tests/scenario/runner.py',
                    '-V',
                    'sahara_tests/unit/scenario/templatevars_complete.ini',
                    'sahara_tests/unit/scenario/vanilla2_7_1.yaml.mako']
        runner.main()

    @mock.patch('sys.exit', return_value=None)
    def test_runner_validate(self, mock_sys):
        sys.argv = ['sahara_tests/scenario/runner.py',
                    '--validate',
                    '-V',
                    'sahara_tests/unit/scenario/templatevars_complete.ini',
                    'sahara_tests/unit/scenario/vanilla2_7_1.yaml.mako']
        runner.main()

    @mock.patch('sahara_tests.scenario.validation.validate')
    @mock.patch('subprocess.Popen',
                return_value=_create_subprocess_communicate_mock())
    @mock.patch('sys.exit', return_value=None)
    def test_runner_from_args(self, mock_sys, mock_sub, mock_validate):
        sys.argv = ['sahara_tests/scenario/runner.py',
                    'sahara_tests/unit/scenario/vanilla2_7_1.yaml.mako',
                    '--os-username', 'demo', '--os-password', 'demopwd',
                    '--os-project-name', 'demo',
                    '--os-auth-url', 'localhost/v2.0',
                    '--args', 'network_type:neutron',
                    'network_private_name:private',
                    'network_public_name:public',
                    'vanilla_26_image:hadoop_2_6_latest',
                    'ci_flavor_id:2']
        runner.main()
        expected = {
            'os_username': 'demo',
            'os_password': 'demopwd',
            'os_tenant': 'demo',
            'os_auth_url': 'localhost/v2.0'
        }
        self.assertTrue(self._isDictContainSubset(
            expected, mock_validate.call_args_list[0][0][0]['credentials']))

    @mock.patch('subprocess.Popen',
                return_value=_create_subprocess_communicate_mock())
    @mock.patch('sys.exit', return_value=None)
    def test_replace_value_args(self, mock_sys, mock_sub):
        sys.argv = ['sahara_tests/scenario/runner.py',
                    '-V',
                    'sahara_tests/unit/scenario/templatevars_complete.ini',
                    'sahara_tests/unit/scenario/vanilla2_7_1.yaml.mako',
                    '--args',
                    'network_type:test']
        with testtools.ExpectedException(exceptions.ValidationError):
            runner.main()

    @mock.patch('sahara_tests.scenario.validation.validate')
    @mock.patch('subprocess.Popen',
                return_value=_create_subprocess_communicate_mock())
    @mock.patch('sys.exit', return_value=None)
    def test_default_templates_non_plugin(self, mock_sys, mock_sub,
                                          mock_validate):
        sys.argv = ['sahara_tests/scenario/runner.py',
                    '-V',
                    'sahara_tests/unit/scenario/templatevars_complete.ini',
                    '-p', 'transient', '--os-username', 'demo',
                    '--os-password', 'demopwd',
                    '--os-project-name', 'demo',
                    '--os-auth-url', 'http://127.0.0.1:5000/v2']
        runner.main()

    @mock.patch('sahara_tests.scenario.validation.validate')
    @mock.patch('subprocess.Popen',
                return_value=_create_subprocess_communicate_mock())
    @mock.patch('sys.exit', return_value=None)
    def test_default_templates_negative(self, mock_sys, mock_sub,
                                        mock_validate):
        sys.argv = ['sahara_tests/scenario/runner.py',
                    '-V',
                    'sahara_tests/unit/scenario/templatevars_complete.ini',
                    '-p', 'vanilla', '--os-username', 'demo',
                    '--os-password', 'demopwd',
                    '--os-project-name', 'demo',
                    '--os-auth-url', 'http://127.0.0.1:5000/v2']
        with testtools.ExpectedException(ValueError):
            runner.main()

    @mock.patch('sahara_tests.scenario.validation.validate')
    @mock.patch('subprocess.Popen',
                return_value=_create_subprocess_communicate_mock())
    @mock.patch('sys.exit', return_value=None)
    def test_default_templates(self, mock_sys, mock_sub, mock_validate):
        sys.argv = ['sahara_tests/scenario/runner.py',
                    '-V',
                    'sahara_tests/unit/scenario/templatevars_complete.ini',
                    '-p', 'spark', '-v', '2.2', '-r', 'queens',
                    '--os-username', 'demo', '--os-password', 'demopwd',
                    '--os-project-name', 'demo',
                    '--os-auth-url', 'http://127.0.0.1:5000/v2']
        runner.main()
        self.assertEqual('spark',
                         mock_validate.call_args[0][0]['clusters'][0][
                             'plugin_name'])
        self.assertEqual('2.2',
                         mock_validate.call_args[0][0]['clusters'][0][
                             'plugin_version'])

    @mock.patch('subprocess.Popen',
                return_value=_create_subprocess_communicate_mock())
    @mock.patch('sys.exit', return_value=None)
    def test_count(self, mock_sys, mock_sub):
        sys.argv = ['sahara_tests/scenario/runner.py',
                    '-V',
                    'sahara_tests/unit/scenario/templatevars_complete.ini',
                    '-p', 'spark', '-v', '2.2', '--release', 'queens',
                    '--count', '4',
                    '--os-username', 'demo', '--os-password', 'demopwd',
                    '--os-project-name', 'demo',
                    '--os-auth-url', 'http://127.0.0.1:5000/v2']
        runner.main()

    @mock.patch('subprocess.Popen',
                return_value=_create_subprocess_communicate_mock())
    @mock.patch('sys.exit', return_value=None)
    def test_run_dir(self, mock_sys, mock_sub):
        sys.argv = ['sahara_tests/scenario/runner.py',
                    '-V',
                    'sahara_tests/unit/scenario/templatevars_complete.ini',
                    'sahara_tests/scenario/defaults/queens',
                    'sahara_tests/scenario/defaults/edp.yaml.mako',
                    '--os-username', 'demo', '--os-password', 'demopwd',
                    '--os-project-name', 'demo',
                    '--os-auth-url', 'http://127.0.0.1:5000/v2', '--args',
                    'ambari_24_image:ambari', 'fake_plugin_image:fake',
                    'mapr_520mrv2_image:mapr', 'cdh_570_image:cdh',
                    'cdh_590_image:cdh', 'cdh_5110_image:cdh',
                    'spark_210_image:spark', 'spark_22_image:spark',
                    'storm_101_image:storm', 'storm_110_image:storm',
                    'vanilla_282_image:vanilla']
        runner.main()

    @mock.patch('sahara_tests.scenario.validation.validate')
    @mock.patch('subprocess.Popen',
                return_value=_create_subprocess_communicate_mock())
    @mock.patch('sys.exit', return_value=None)
    def test_credentials_envvars(self, mock_sys, mock_sub, mock_validate):
        username = os.environ.get('OS_USERNAME', '')
        password = os.environ.get('OS_PASSWORD', '')
        auth_url = os.environ.get('OS_AUTHURL', '')
        project_name = os.environ.get('OS_PROJECT_NAME', '')
        os.environ['OS_USERNAME'] = 'demo_env'
        os.environ['OS_PASSWORD'] = 'demopwd_env'
        os.environ['OS_AUTH_URL'] = 'http://localhost:5000/v2.0'
        os.environ['OS_PROJECT_NAME'] = 'project_env'
        sys.argv = ['sahara_tests/scenario/runner.py',
                    '-V',
                    'sahara_tests/unit/scenario/templatevars_complete.ini',
                    '-p', 'spark', '-v', '1.3.1', '--release', 'liberty',
                    '--count', '4']
        runner.main()
        expected = {
            'os_username': 'demo_env',
            'os_password': 'demopwd_env',
            'os_tenant': 'project_env',
            'os_auth_url': 'http://localhost:5000/v2.0'
        }
        self.assertTrue(self._isDictContainSubset(
            expected, mock_validate.call_args_list[0][0][0]['credentials']))

        os.environ['OS_USERNAME'] = username
        os.environ['OS_PASSWORD'] = password
        os.environ['OS_AUTHURL'] = auth_url
        os.environ['OS_PROJECT_NAME'] = project_name

    @mock.patch('sahara_tests.scenario.validation.validate')
    @mock.patch('subprocess.Popen',
                return_value=_create_subprocess_communicate_mock())
    @mock.patch('sys.exit', return_value=None)
    def test_credentials_clouds(self, mock_sys, mock_sub, mock_validate):
        unit_dir = pkg.resource_filename(version.version_info.package,
                                         'unit')
        os_client_config_file = os.environ.get('OS_CLIENT_CONFIG_FILE', '')
        os.environ['OS_CLIENT_CONFIG_FILE'] = os.path.join(unit_dir,
                                                           'scenario',
                                                           'clouds.yaml')
        sys.argv = ['sahara_tests/scenario/runner.py',
                    '-V',
                    'sahara_tests/unit/scenario/templatevars_complete.ini',
                    '-p', 'spark', '-v', '1.0.0', '--count', '4',
                    '--os-cloud', 'scenario_test']
        runner.main()
        expected = {
            'os_username': 'demo_cloud',
            'os_password': 'demo_cloud_pwd',
            'os_tenant': 'demo_cloud_project',
            'os_auth_url': 'http://localhost:5000/v2.0'
        }
        self.assertTrue(self._isDictContainSubset(
            expected, mock_validate.call_args_list[0][0][0]['credentials']))
        os.environ['OS_CLIENT_CONFIG_FILE'] = os_client_config_file

