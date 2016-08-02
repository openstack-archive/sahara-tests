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
from tempest.test import BaseTestCase


class ClientTestBase(base.ClientTestBase):
    """Base class for saharaclient tests.

    Establishes the sahara client and retrieves the essential environment
    information.
    """

    def _get_clients(self):
        cli_dir = os.environ.get('OS_SAHARA_TESTS_DIR', '')
        if not cli_dir:
            # if this is executed in a virtualenv, the command installed there
            # will be the first one.
            paths = os.environ.get('PATH').split(':')
            for path in paths:
                client_candidate = os.path.join(path, 'openstack')
                if os.path.isfile(client_candidate) and os.access(
                        client_candidate, os.X_OK):
                    cli_dir = path
                    break

        self.client_manager_admin = BaseTestCase.get_client_manager('admin')
        auth_provider = self.client_manager_admin.auth_provider

        return base.CLIClient(
            username=auth_provider.credentials.get('username'),
            password=auth_provider.credentials.get('password'),
            tenant_name=auth_provider.credentials.get('tenant_name'),
            uri=auth_provider.base_url({'service': 'identity'}),
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
''' % (command, name))
        # lower() is required because "command" in the result string could
        # have the first letter capitalized.
        self.assertEqual(delete_cmd.lower(), result.lower())

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
