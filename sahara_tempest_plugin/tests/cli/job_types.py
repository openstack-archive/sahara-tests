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

from os import remove

from tempest.lib.common.utils import data_utils

from sahara_tempest_plugin.tests.cli import base

GET_CONFIG_RESULT = '"%s" job configs were saved in "%s"file'


class SaharaJobTypeCLITest(base.ClientTestBase):

    def openstack_job_type_list(self):
        self.assertTableStruct(self.listing_result('job type list'), [
            'Name',
            'Plugins'
        ])

    def openstack_job_type_configs_get(self, flag=None):
        list_job_type = self.listing_result('job type list')
        job_type_names = [p['Name'] for p in list_job_type]
        if len(job_type_names) == 0:
            raise self.skipException('No job types to get configs')
        cmd = 'job type configs get'
        type_name = job_type_names[0]
        if flag == 'file':
            file_name = data_utils.rand_name('filename')
            cmd = '%s --%s %s %s' % (cmd, flag, file_name, type_name)
        else:
            file_name = type_name
            cmd = '%s %s' % (cmd, type_name)
        result = self.openstack('dataprocessing %s' % cmd)
        expected_result = GET_CONFIG_RESULT % (type_name, file_name)
        self.assertEqual(result, expected_result)
        remove(file_name)

    def filter_job_type_in_list(self):
        """Filter job types list with --column flag"""
        list_job_types = self.listing_result('job type list --column Name')
        self.assertTableStruct(list_job_types, ['Name'])
