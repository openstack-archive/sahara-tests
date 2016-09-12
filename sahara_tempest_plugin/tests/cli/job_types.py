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

from sahara_tempest_plugin.tests.cli import base


class SaharaJobTypeCLITest(base.ClientTestBase):

    def openstack_job_type_list(self):
        self.assertTableStruct(self.listing_result('job type list'), [
            'Name',
            'Plugins'
        ])

    def openstack_job_type_configs_get(self):
        list_job_type = self.listing_result('job type list')
        job_type_names = [p['Name'] for p in list_job_type]
        if len(job_type_names) == 0:
            raise self.skipException('No job types to get configs')
        self.assertTableStruct(self.listing_result(
            ''.join(['job type configs get ', job_type_names[0]])), [
            'Field',
            'Value'
        ])
