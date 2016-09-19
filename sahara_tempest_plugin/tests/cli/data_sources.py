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
from tempest.lib.common.utils import data_utils


class SaharaDataSourceCLITest(base.ClientTestBase):

    def openstack_data_source_list(self):
        self.assertTableStruct(self.listing_result('data source list'), [
            'Name',
            'Type'
        ])

    def openstack_data_source_create(self):
        data_source_name = data_utils.rand_name('data-source')
        flag = ("%(name)s %(type)s %(url)s %(user)s %(pass)s"
                % {'type': '--type hdfs',
                   'url': '--url hdfs://demo/input.tar.gz',
                   'user': ' --user cli-test',
                   'pass': '--password cli',
                   'name': data_source_name})
        self.assertTableStruct(
            self.listing_result('data source create %s' % flag),
            [
                'Field',
                'Value'
            ])
        return data_source_name

    def openstack_data_source_show(self, data_source_name):
        self.find_in_listing(
            self.listing_result('data source show %s' % data_source_name),
            data_source_name)

    def openstack_data_source_update(self, data_source_name):
        self.assertTableStruct(
            self.listing_result('data source update %s' % data_source_name),
            [
                'Field',
                'Value'
            ])

    def openstack_data_source_delete(self, data_source_name):
        self.check_if_delete('data source', data_source_name)
