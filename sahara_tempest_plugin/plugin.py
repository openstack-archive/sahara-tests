# Copyright 2016 Red Hat, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import os

from tempest import config
from tempest.test_discover import plugins

from sahara_tempest_plugin import config as sahara_config


class SaharaTempestPlugin(plugins.TempestPlugin):
    def load_tests(self):
        base_path = os.path.split(os.path.dirname(
            os.path.abspath(__file__)))[0]
        test_dir = "sahara_tempest_plugin/tests"
        full_test_dir = os.path.join(base_path, test_dir)
        return full_test_dir, base_path

    def register_opts(self, conf):
        conf.register_opt(sahara_config.service_option,
                          group='service_available')
        conf.register_group(sahara_config.data_processing_group)
        conf.register_opts(sahara_config.DataProcessingGroup +
                           sahara_config.DataProcessingAdditionalGroup,
                           sahara_config.data_processing_group)

        conf.register_group(sahara_config.data_processing_feature_group)
        conf.register_opts(sahara_config.DataProcessingFeaturesGroup,
                           sahara_config.data_processing_feature_group)

    def get_opt_lists(self):
        return [
            (sahara_config.data_processing_group.name,
             sahara_config.DataProcessingGroup),
            (sahara_config.data_processing_feature_group.name,
             sahara_config.DataProcessingFeaturesGroup),
        ]

    def get_service_clients(self):
        data_processing_config = (
            config.service_client_config('data-processing'))

        params = {
            'name': 'data_processing',
            'service_version': 'data_processing.v1_1',
            'module_path':
                'sahara_tempest_plugin.services.data_processing.v1_1',
            'client_names': ['DataProcessingClient']
        }
        params.update(data_processing_config)
        params_v2 = {
            'name': 'data_processing_v2',
            'service_version': 'data_processing.v2',
            'module_path':
                'sahara_tempest_plugin.services.data_processing.v2',
            'client_names': ['DataProcessingClient']
        }
        params_v2.update(data_processing_config)
        return [params, params_v2]
