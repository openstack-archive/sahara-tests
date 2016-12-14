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
        flags = ("%(ngt_name)s %(plugin)s %(plugin-version)s "
                 "%(processes)s %(flavor)s %(floating-pool)s"
                 % {'floating-pool': ' --floating-ip-pool %s' % id_net_pool,
                    'flavor': ' --flavor %s' % flavor_id,
                    'processes': ' --processes datanode',
                    'plugin-version': ' --plugin-version %s'
                                      % plugin['Versions'],
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
        new_node_group_name = None
        cmd = 'node group template update %s' % node_group_name
        if update_field == 'name':
            new_node_group_name = data_utils.rand_name(node_group_name)
            update_cmd = '--%s %s' % (update_field, new_node_group_name)
        elif update_field:
            # here we check only updating with public/protected flags for now
            update_cmd = '--%s' % update_field
        else:
            # if update_field is None, update_command should be empty
            update_cmd = ''
        self.assertTableStruct(
            self.listing_result('%s %s' % (cmd, update_cmd)), [
                'Field',
                'Value'
            ])
        return new_node_group_name

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
