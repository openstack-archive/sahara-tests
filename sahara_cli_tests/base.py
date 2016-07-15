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

from tempest.lib.cli import base


class ClientTestBase(base.ClientTestBase):
    """Base class for saharaclient tests.

    Establishes the sahara client and retrieves the essential environment
    information.
    """

    def _get_clients(self):
        cli_dir = os.environ.get(
            'OS_SAHARA_TESTS_DIR',
            os.path.join(os.path.abspath('.'), '.tox/cli-tests/bin'))

        return base.CLIClient(
            username=os.environ.get('OS_USERNAME'),
            password=os.environ.get('OS_PASSWORD'),
            tenant_name=os.environ.get('OS_TENANT_NAME'),
            uri=os.environ.get('OS_AUTH_URL'),
            cli_dir=cli_dir)

    def openstack(self, *args, **kwargs):
        return self.clients.openstack(*args, **kwargs)

    def listing_result(self, command):
        command_for_item = self.openstack('dataprocessing', params=command)
        result = self.parser.listing(command_for_item)
        return result

    def find_in_listing(self, result, name):
        check_table = None
        for line in result:
            if line['Field'] == 'Name':
                self.assertEqual(line['Value'], name)
                check_table = True
        if check_table is None:
            raise self.skipException('No table to show information')

    def check_if_delete(self, command, name):
        delete_cmd = self.openstack('dataprocessing %s delete' % command,
                                    params=name)
        result = ('''\
%s "%s" has been removed successfully.
''' % command % name)
        self.assertEqual(delete_cmd, result)

    def find_fake_plugin(self):
        found_plugin = None
        plugins = self.listing_result('plugin list')
        for plugin in plugins:
            if plugin['Name'] == 'fake':
                found_plugin = plugin
        if found_plugin is None:
            raise self.skipException('No available plugins for testing')
        return found_plugin

    def find_id_of_pool(self):
        floating_pool_list = self.openstack('ip floating pool list')
        floating_pool = self.parser.listing(floating_pool_list)
        network_list = self.openstack('network list')
        networks = self.parser.listing(network_list)
        network_name = [p['Name'] for p in networks]
        pools_name = [p['Name'] for p in floating_pool]
        if not network_name:
            raise self.skipException('Network list is empty')
        if not pools_name:
            raise self.skipException('Floating pool ip list is empty')
        name_net_pool = None
        id_net_pool = None
        for net_name in network_name:
            for pool_name in pools_name:
                if net_name == pool_name:
                    name_net_pool = net_name
        if name_net_pool is None:
            raise self.skipException('Network list and floating pool ip list'
                                     ' dont have common networks')
        for network in networks:
            if network['Name'] == name_net_pool:
                id_net_pool = network['ID']
        return id_net_pool
