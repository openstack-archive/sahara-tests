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

from tempest.lib.common.utils import data_utils

from sahara_tempest_plugin.tests.cli import base


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
        plugin_version = plugin['Versions'].split(',')[0].strip()
        flags = ("%(ngt_name)s %(plugin)s %(plugin-version)s "
                 "%(processes)s %(flavor)s %(floating-pool)s"
                 % {'floating-pool': ' --floating-ip-pool %s' % id_net_pool,
                    'flavor': ' --flavor %s' % flavor_id,
                    'processes': ' --processes datanode',
                    'plugin-version': ' --plugin-version %s' % plugin_version,
                    'plugin': ' --plugin %s' % plugin['Name'],
                    'ngt_name': '--name %s' % node_group_name})
        self.assertTableStruct(
            self.listing_result('node group template create %s' % flags), [
                'Field',
                'Value'
            ])
        return node_group_name

    def openstack_node_group_template_show(self, node_group_name):
        self.find_in_listing(
            self.listing_result('node group template show %s'
                                % node_group_name),
            node_group_name)

    def openstack_node_group_template_update(self, node_group_name,
                                             update_field=None):
        """Update node group template with necessary parameters
        Args:
            node_group_name (str): name of node group to update
            update_field (str): param how to update the node group. Using
            this arg, there are several available updates of node group:
            name, public/private, protected/unprotected
        """
        cmd = 'node group template'
        if update_field == 'name':
            new_node_group_name = self.update_resource_value(cmd,
                                                             node_group_name,
                                                             '--name')
            return new_node_group_name
        elif update_field in ('protected', 'unprotected'):
            # here we check only updating with public/protected flags for now
            update_cmd = 'update %s --%s' % (node_group_name, update_field)
            result = self.listing_result('%s %s' % (cmd, update_cmd))
            is_protected_value = str(update_field == 'protected')
            self.find_in_listing(result, is_protected_value, 'is protected')
            self.assertTableStruct(result, ['Field', 'Value'])

    def openstack_node_group_template_delete(self, node_group_name):
        self.check_if_delete('node group template', node_group_name)

    def negative_delete_removed_node_group(self, node_group_name):
        """Test to remove already deleted node group template"""
        command_to_execute = 'node group template delete'
        self.check_negative_scenarios(base.TEMPEST_ERROR_MESSAGE,
                                      command_to_execute,
                                      node_group_name)

    def negative_try_to_delete_protected_node_group(self, node_group_name):
        """Test to delete protected node group template"""
        self.openstack_node_group_template_update(node_group_name,
                                                  update_field='protected')
        error_message = ("NodeGroupTemplate with id '%s' could not be deleted "
                         "because it's marked as protected"
                         % self._get_resource_id('node group template',
                                                 node_group_name))
        command_to_execute = 'node group template delete'
        self.check_negative_scenarios(error_message,
                                      command_to_execute,
                                      node_group_name)
        self.openstack_node_group_template_update(node_group_name,
                                                  update_field='unprotected')

    def filter_node_group_list_with_plugin(self):
        """Test to filter node group templates with the plugin"""
        plugins_list = self.listing_result('plugin list')
        plugins_names = [p['Name'] for p in plugins_list]
        if len(plugins_names) == 0:
            raise self.skipException('No plugin to filter node group')
        filter_cmd = self.listing_result(
            'node group template list --plugin %s' % plugins_names[0])
        for ng in filter_cmd:
            self.assertEqual(plugins_names[0], ng['Plugin name'])
        self.assertTableStruct(filter_cmd, [
            'Name',
            'Id',
            'Plugin version',
            'Plugin name'
        ])
