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


class SaharaNodeGroupCLITest(base.ClientTestBase):

    def openstack_node_group_template_list(self):
        self.assertTableStruct(
            self.listing_result('node group template list'), [
                'Name',
                'Id',
                'Plugin version',
                'Plugin name'
            ])

    def openstack_node_group_template_create(self, ng_type, flavor_id):
        plugin = self.get_default_plugin()
        id_net_pool = self.find_id_of_pool()
        node_group_name = data_utils.rand_name(ng_type)
        flags = ("%(ngt_name)s %(plugin)s %(plugin-version)s "
                 "%(processes)s %(flavor)s %(floating-pool)s"
                 % {'floating-pool': ''.join([' --floating-ip-pool ',
                                              id_net_pool]),
                    'flavor': ''.join([' --flavor ', flavor_id]),
                    'processes': ' --processes datanode',
                    'plugin-version':
                        ''.join([' --plugin-version ', plugin['Versions']]),
                    'plugin': ''.join([' --plugin ', plugin['Name']]),
                    'ngt_name': ''.join(['--name ', node_group_name])})
        self.assertTableStruct(
            self.listing_result(''.join(['node group template create ',
                                         flags])), [
                'Field',
                'Value'
            ])
        return node_group_name

    def openstack_node_group_template_show(self, node_group_name):
        self.find_in_listing(
            self.listing_result(
                ''.join(['node group template show ', node_group_name])),
            node_group_name)

    def openstack_node_group_template_update(self, node_group_name):
        new_node_group_name = ''.join([node_group_name, '1'])
        self.assertTableStruct(
            self.listing_result(
                ''.join(['node group template update --name ',
                         new_node_group_name, ' ',
                         node_group_name])), [
                'Field',
                'Value'
            ])
        return new_node_group_name

    def openstack_node_group_template_delete(self, node_group_name):
        self.check_if_delete('node group template', node_group_name)
