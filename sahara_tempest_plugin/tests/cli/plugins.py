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

from os import path
from os import remove
import re
import tempfile

from oslo_serialization import jsonutils

from sahara_tempest_plugin.tests.cli import base


class SaharaPluginCLITest(base.ClientTestBase):

    def openstack_plugin_list(self):
        self.assertTableStruct(self.listing_result('plugin list'), [
            'Name',
            'Versions'
        ])

    def openstack_plugin_show(self):
        list_plugin = self.listing_result('plugin list')
        name = [p['Name'] for p in list_plugin]
        if len(name) == 0:
            raise self.skipException('No plugins to show')
        self.assertTableStruct(
            self.listing_result(''.join(['plugin show ', name[0]])), [
                'Field',
                'Value'
            ])

    def openstack_plugin_configs_get(self):
        list_plugin = self.listing_result('plugin list')
        name = [p['Name'] for p in list_plugin]
        version = [p['Versions'] for p in list_plugin]
        if len(name) == 0:
            raise self.skipException('No plugin to get configs')
        plugin_name = name[0]
        plugin_version = version[0].split(',')[0].strip()

        configs_file = '%s-%s' % (plugin_name, plugin_version)
        if path.exists(configs_file):
            remove(configs_file)

        outmsg = self.openstack('dataprocessing plugin configs get',
                                params='%s %s' % (plugin_name, plugin_version))
        outfile_match = re.search('configs was saved in "(.+)"', outmsg)
        if outfile_match:
            configs_file = outfile_match.group(1)
        else:
            configs_file = '%s-%s' % (plugin_name, plugin_version)

        result = path.exists(configs_file)
        self.assertTrue(result)
        remove(configs_file)

    def openstack_plugin_update(self):
        # check plugin list and 'fake' is available
        list_plugin = self.listing_result('plugin list')
        name = [p['Name'] for p in list_plugin]
        if len(name) == 0:
            raise self.skipException('No plugin to update')
        if 'fake' not in name:
            raise self.skipException('fake plugin is unavailable')

        # update value of "hidden:status" to False
        update_dict = {'plugin_labels': {'hidden': {'status': False}}}
        self._update_with_json_file(update_dict)

        # update value and verified it
        update_dict = {'plugin_labels': {'hidden': {'status': True}}}
        update_info = self._update_with_json_file(update_dict)
        update_dict = jsonutils.loads(update_info)
        self.assertTrue(update_dict['Plugin: hidden'])

    def _update_with_json_file(self, update_dict):
        update_info = jsonutils.dumps(update_dict)
        tmp_file = tempfile.mkstemp(suffix='.json')[1]
        with open(tmp_file, 'w+') as fd:
            fd.write(update_info)
        update_result = self.openstack('dataprocessing plugin '
                                       'update -f json fake',
                                       params=tmp_file)
        remove(tmp_file)
        return update_result
