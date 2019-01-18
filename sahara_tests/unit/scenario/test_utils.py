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

import mock
import testtools

from sahara_tests.scenario import utils


class UtilsGenerateConfigTest(testtools.TestCase):

    def setUp(self):
        super(UtilsGenerateConfigTest, self).setUp()
        self._cluster_config = {
            "clusters": [{
                "edp_jobs_flow": [
                    "pig_all",
                    {
                        "name": "pig_feat2",
                        "features": ["feat2"]
                    },
                    {
                        "name": "pig_featmulti",
                        "features": ["feat1", "feat2"]
                    },
                ]
            }],
            "edp_jobs_flow": {
                "pig_all": [
                    {
                        "type": "Pig",
                        "input_datasource": {
                            "type": "swift",
                            "source": "sahara_tests/scenario/defaults/"
                                      "edp-examples/edp-pig/"
                                      "top-todoers/data/input"
                        },
                        "output_datasource": {
                            "type": "hdfs",
                            "destination": "/user/hadoop/edp-output"
                        },
                        "main_lib": {
                            "type": "swift",
                            "source": "sahara_tests/scenario/defaults/"
                                      "edp-examples/edp-pig/"
                                      "top-todoers/example.pig"
                        }
                    }
                ],
                "pig_feat2": [
                    {
                        "type": "Pig",
                        "input_datasource": {
                            "type": "swift",
                            "source": "sahara_tests/scenario/defaults/"
                                      "edp-examples/edp-pig/"
                                      "top-todoers/data/input"
                        },
                        "output_datasource": {
                            "type": "hdfs",
                            "destination": "/user/hadoop/edp-output"
                        },
                        "main_lib": {
                            "type": "swift",
                            "source": "sahara_tests/scenario/defaults/"
                                      "edp-examples/edp-pig/"
                                      "top-todoers/example.pig"
                        }
                    }
                ],
                "pig_featmulti": [
                    {
                        "type": "Pig",
                        "input_datasource": {
                            "type": "swift",
                            "source": "sahara_tests/scenario/defaults/"
                                      "edp-examples/edp-pig/"
                                      "top-todoers/data/input"
                        },
                        "output_datasource": {
                            "type": "hdfs",
                            "destination": "/user/hadoop/edp-output"
                        },
                        "main_lib": {
                            "type": "swift",
                            "source": "sahara_tests/scenario/defaults/"
                                      "edp-examples/edp-pig/"
                                      "top-todoers/example.pig"
                        }
                    }
                ]
            }
        }

    @mock.patch('sahara_tests.scenario.utils.read_scenario_config')
    def test_generate_config_feature(self, m_readscenarioconfig):
        """Check the generate_config method when features are specified."""
        m_readscenarioconfig.return_value = self._cluster_config
        # "template_variables" can be empty because read_scenario_config,
        # which is its only users, is a mock variable.
        # "files" is used to loop over the read keys, so at one fake
        # file name is needed.
        result = utils.generate_config(['dummyfile.yaml'], None,
                                       {'credentials': {}}, False,
                                       features_list=['feat1'])
        self.assertIn('clusters', result)
        self.assertEqual(set(result['clusters'][0]['edp_jobs_flow']),
                         set(["pig_all", "pig_featmulti"]))

    @mock.patch('sahara_tests.scenario.utils.read_scenario_config')
    def test_generate_config_nofeatures(self, m_readscenarioconfig):
        """Check the generate_config method when features are specified."""
        m_readscenarioconfig.return_value = self._cluster_config
        # "template_variables" can be empty because read_scenario_config,
        # which is its only users, is a mock variable.
        # "files" is used to loop over the read keys, so at one fake
        # file name is needed.
        result = utils.generate_config(['dummyfile.yaml'], None,
                                       {'credentials': {}}, False,
                                       features_list=[])
        self.assertIn('clusters', result)
        self.assertEqual(set(result['clusters'][0]['edp_jobs_flow']),
                         set(["pig_all"]))

    @mock.patch('sahara_tests.scenario.utils.read_scenario_config')
    def test_generate_config_singlejob_str(self, m_readscenarioconfig):
        """Check the generate_config method when the cluster runs only
        a single job defined as string and not as list."""
        cluster_config_singlejob_str = self._cluster_config
        cluster_config_singlejob_str['clusters'][0]["edp_jobs_flow"] = \
            'pig_all'
        m_readscenarioconfig.return_value = cluster_config_singlejob_str
        # "template_variables" can be empty because read_scenario_config,
        # which is its only users, is a mock variable.
        # "files" is used to loop over the read keys, so at one fake
        # file name is needed.
        result = utils.generate_config(['dummyfile.yaml'], None,
                                       {'credentials': {}}, False,
                                       features_list=[])
        self.assertIn('clusters', result)
        self.assertEqual(set(result['clusters'][0]['edp_jobs_flow']),
                         set(["pig_all"]))

    @mock.patch('sahara_tests.scenario.utils.read_scenario_config')
    def test_generate_config_unknownjob(self, m_readscenarioconfig):
        """Check the generate_config method when an unknown job is specified,
        thus leading to an exception."""
        cluster_config_unknownjob = self._cluster_config
        cluster_config_unknownjob['clusters'][0]["edp_jobs_flow"].append(
            'unknown_job')
        m_readscenarioconfig.return_value = cluster_config_unknownjob
        # "template_variables" can be empty because read_scenario_config,
        # which is its only users, is a mock variable.
        # "files" is used to loop over the read keys, so at one fake
        # file name is needed.
        self.assertRaises(ValueError, utils.generate_config,
                          ['dummyfile.yaml'], None, {'credentials': {}},
                          False, features_list=[])


class UtilsTemplatesTest(testtools.TestCase):

    def test_get_default_templates_noversion_nofeatures(self):
        """Check the list of automatically discovered templates
        when the plugin does not require versions and
        there are no features specified."""
        found_templates = utils.get_default_templates('fake', None, None,
                                                      ['conffile.yaml'])
        expected_templates = (
            utils.DEFAULT_TEMPLATE_VARS +
            [os.path.join(utils.TEST_TEMPLATE_DIR, 'fake.yaml.mako'),
             'conffile.yaml']
        )
        self.assertListEqual(found_templates, expected_templates)

    def test_get_default_templates_missingversion(self):
        """Check the list of automatically discovered templates
        when the plugin requires a version but it was not specified."""
        self.assertRaises(ValueError, utils.get_default_templates,
                          'vanilla', None, None, ['conffile.yaml'])

    @mock.patch('os.path.exists', side_effect=[True, False, True, True])
    def test_get_default_templates_version_release_features(self, m_exist):
        """Check the list of automatically discovered templates
        when the plugin requires a version, a release is specified and
        there are features specified."""
        found_templates = utils.get_default_templates('vanilla', '2.7.1',
                                                      'rocky',
                                                      ['conffile.yaml'],
                                                      ['feat1', 'feat2'])
        expected_templates = (
            utils.DEFAULT_TEMPLATE_VARS +
            [os.path.join(utils.TEST_TEMPLATE_DIR, 'rocky',
                          'vanilla-2.7.1.yaml.mako'),
             os.path.join(utils.TEST_TEMPLATE_DIR,
                          'credentials_feat1.yaml.mako'),
             os.path.join(utils.TEST_TEMPLATE_DIR,
                          'credentials_feat2.yaml.mako'),
             os.path.join(utils.TEST_TEMPLATE_DIR,
                          'edp_feat2.yaml.mako'),
             'conffile.yaml']
        )
        self.assertListEqual(found_templates, expected_templates)
