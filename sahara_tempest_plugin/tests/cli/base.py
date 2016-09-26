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
import fixtures
import time

from tempest import config
from tempest.lib.cli import base
from tempest.test import BaseTestCase
from tempest.lib import exceptions as exc

from sahara_tempest_plugin.common import plugin_utils

TEMPEST_CONF = config.CONF
DEL_RESULT = '''\
{} "{}" has been removed successfully.
'''


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
        self.project_network = BaseTestCase.get_tenant_network('admin')

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
        result = DEL_RESULT.format(command, name)
        # lower() is required because "command" in the result string could
        # have the first letter capitalized.
        self.assertEqual(delete_cmd.lower(), result.lower())

    def get_default_plugin(self):
        plugins = self.listing_result('plugin list')
        default_plugin_name = plugin_utils.get_default_plugin()
        for plugin in plugins:
            if plugin['Name'] == default_plugin_name:
                return plugin
        raise self.skipException('No available plugins for testing')

    def find_id_of_pool(self):
        floating_pool_list = self.openstack('network list --external')
        floating_pool = self.parser.listing(floating_pool_list)
        if not floating_pool:
            raise self.skipException('Floating pool ip list is empty')
        # if not empty, there should be at least one element
        return floating_pool[0]['ID']

    def _get_cluster_status(self, cluster_name):
        status = None
        show_cluster = self.listing_result(''.join(['cluster show ',
                                                    cluster_name]))
        for line in show_cluster:
            if line['Field'] == 'Status':
                status = line['Value']
        if status is None:
            raise self.skipException('Can not find the cluster to get its '
                                     'status')
        return status

    def _poll_cluster_status(self, cluster_name):
        with fixtures.Timeout(TEMPEST_CONF.data_processing.cluster_timeout,
                              gentle=True):
            while True:
                status = self._get_cluster_status(cluster_name)
                if status == 'Active':
                    break
                if status == 'Error':
                    raise exc.TempestException("Cluster in %s state" % status)
                time.sleep(3)

    def wait_for_resource_deletion(self, name, type):
        # type can be cluster, cluster template or node group template string
        name_exist = False
        # if name exists in the command "type list" than tests should fail
        with fixtures.Timeout(300, gentle=True):
            while True:
                list_of_types = self.listing_result(''.join([type, ' list']))
                list_names = [p['Name'] for p in list_of_types]
                for resource_name in list_names:
                    if resource_name == name:
                        name_exist = True
                if not name_exist:
                    break
