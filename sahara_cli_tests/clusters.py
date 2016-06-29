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

from sahara_cli_tests import base
from tempest.lib.common.utils import data_utils


class SaharaClusterCLITest(base.ClientTestBase):

    def openstack_cluster_list(self):
        self.assertTableStruct(self.listing_result('cluster list'), [
            'Name',
            'Id',
            'Plugin name',
            'Plugin version',
            'Status'
        ])

    def openstack_cluster_create(self, cluster_template_name, image_name):
        cluster_name = data_utils.rand_name('cluster')
        id_net_pool = self.find_id_of_pool()
        flags = ("%(name)s %(cl-tm)s %(image)s %(network)s"
                 % {'network': ''.join([' --neutron-network ', id_net_pool]),
                    'image': ''.join([' --image ', image_name]),
                    'cl-tm': ''.join([' --cluster-template ',
                                      cluster_template_name]),
                    'name': ''.join([' --name ', cluster_name])})
        self.assertTableStruct(
            self.listing_result(''.join(['cluster create ', flags])), [
                'Field',
                'Value'
            ])
        return cluster_name

    def openstack_cluster_delete(self, cluster_name):
        self.assertTableStruct(
            self.listing_result(''.join(['cluster delete ', cluster_name])), [
                'Field',
                'Value'
            ])

    def openstack_cluster_show(self, cluster_name):
        self.find_in_listing(
            self.listing_result(''.join(['cluster show ', cluster_name])),
            cluster_name)
