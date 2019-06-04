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
from tempest import test
from tempest.lib import exceptions as exc
from tempest.lib.auth import IDENTITY_VERSION
from tempest.lib.common.utils import data_utils

from sahara_tempest_plugin.common import plugin_utils

TEMPEST_CONF = config.CONF
DEL_RESULT = '''\
{} "{}" has been removed successfully.
'''
TEMPEST_ERROR_MESSAGE = 'No matches found.'


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

        self.client_manager_admin = \
            test.BaseTestCase.get_client_manager('admin')
        auth_provider = self.client_manager_admin.auth_provider
        self.project_network = test.BaseTestCase.get_tenant_network('admin')

        project_name = auth_provider.credentials.get('project_name')
        if project_name is None:
            project_name = auth_provider.credentials.get('tenant_name')

        # complicated but probably the only way to get the exact type
        # of Identity API version
        if isinstance(auth_provider, IDENTITY_VERSION['v2'][1]):
            identity_api_version = 2
        else:
            identity_api_version = 3

        return base.CLIClient(
            username=auth_provider.credentials.get('username'),
            password=auth_provider.credentials.get('password'),
            tenant_name=project_name,
            uri=auth_provider.base_url({'service': 'identity'}),
            cli_dir=cli_dir,
            user_domain=auth_provider.credentials.get('user_domain_name'),
            project_domain=auth_provider.credentials.get(
                'project_domain_name'),
            identity_api_version=identity_api_version)

    def openstack(self, action, flags='', params='', fail_ok=False,
                  merge_stderr=False):
        if '--os-data-processing-api-version' not in flags:
            flags = flags + '--os-data-processing-api-version %s' % \
                (TEMPEST_CONF.data_processing.api_version_saharaclient)
        return self.clients.openstack(action, flags=flags, params=params,
                                      fail_ok=fail_ok, merge_stderr=False)

    def listing_result(self, command):
        command_for_item = self.openstack('dataprocessing', params=command)
        result = self.parser.listing(command_for_item)
        return result

    def find_in_listing(self, result, value, field='name'):
        for line in result:
            if line['Field'].lower() == field.lower():
                self.assertEqual(line['Value'].lower(), value.lower())
                return
        raise self.skipException('No table to show information')

    def check_if_delete(self, command, name):
        delete_cmd = self.openstack('dataprocessing %s delete' % command,
                                    params=name)
        result = DEL_RESULT.format(command, name)
        # lower() is required because "command" in the result string could
        # have the first letter capitalized.
        self.assertEqual(delete_cmd.lower(), result.lower())

    def update_resource_value(self, command, value, params):
        new_value = data_utils.rand_name(value)
        command = '%s update %s' % (command, value)
        params = '%s %s' % (params, new_value)
        update_result = self.listing_result('%s %s' % (command, params))
        self.find_in_listing(update_result, new_value)
        return new_value

    def delete_resource(self, command, name):
        list_of_resources = self.listing_result('%s list' % command)
        list_of_resource_names = [r['Name'] for r in list_of_resources]
        if name in list_of_resource_names:
            self.openstack('dataprocessing %s delete' % command, params=name)

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
        show_cluster = self.listing_result('cluster show %s' % cluster_name)
        for line in show_cluster:
            if line['Field'] == 'Status':
                status = line['Value']
        if status is None:
            raise self.skipException('Can not find the cluster to get its '
                                     'status')
        return status

    def _get_resource_id(self, resource, resource_name):
        resource_id = None
        show_resource = self.listing_result('%s show %s'
                                            % (resource, resource_name))
        for line in show_resource:
            if line['Field'] == 'Id':
                resource_id = line['Value']
        if resource_id is None:
            raise self.skipException('No such %s exists' % resource)
        return resource_id

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
                list_of_types = self.listing_result('%s list' % type)
                list_names = [p['Name'] for p in list_of_types]
                if name in list_names:
                    name_exist = True
                if not name_exist:
                    break

    def check_negative_scenarios(self, error_message, cmd, name):
        msg_exist = None
        try:
            self.openstack('dataprocessing %s' % cmd, params=name)
        except exc.CommandFailed as e:
            # lower() is required because "result" string could
            # have the first letter capitalized.
            if error_message.lower() in str(e).lower():
                msg_exist = True
            if not msg_exist:
                raise exc.TempestException('"%s" is not a part of output of '
                                           'executed command "%s" (%s)'
                                           % (error_message, cmd, output_msg))
        else:
            raise exc.TempestException('"%s %s" in negative scenarios has '
                                       'been executed without any errors'
                                       % (cmd, name))

    @classmethod
    def tearDownClass(cls):
        if hasattr(super(ClientTestBase, cls), 'tearDownClass'):
            super(ClientTestBase, cls).tearDownClass()
        # this'll be needed as long as BaseTestCase functions
        # are used in this class, otherwise projects, users,
        # networks and routers created won't be deleted
        test.BaseTestCase.clear_credentials()
