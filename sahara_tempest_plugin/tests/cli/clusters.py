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
import fixtures

VERIF_RESULT = '''\
Cluster "%s" health verification has been started.
'''


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
        # FIXME: this is unstable interface, but apparently there are no
        # suitable ready-to-use replacements.
        id_net_project = self.project_network['id']
        flags = ("%(name)s %(cl-tm)s %(image)s %(network)s"
                 % {'network': '--neutron-network %s' % (id_net_project),
                    'image': '--image %s' % (image_name),
                    'cl-tm': '--cluster-template %s' %
                             (cluster_template_name),
                    'name': '--name %s' % (cluster_name)})
        self.assertTableStruct(
            self.listing_result(''.join(['cluster create ', flags])), [
                'Field',
                'Value'
            ])
        self._poll_cluster_status(cluster_name)
        return cluster_name

    def openstack_cluster_delete(self, cluster_name):
        delete_cluster = self.listing_result(''.join(['cluster delete ',
                                                      cluster_name]))
        self.assertTableStruct(delete_cluster, [
            'Field',
            'Value'
        ])

    def openstack_cluster_show(self, cluster_name):
        self.find_in_listing(
            self.listing_result(''.join(['cluster show ', cluster_name])),
            cluster_name)

    def openstack_cluster_update(self, cluster_name):
        self.assertTableStruct(
            self.listing_result(''.join(['cluster update ',
                                         '--description cli-tests ',
                                         cluster_name])), [
                'Field',
                'Value'
            ])

    def openstack_cluster_verification_show(self, cluster_name):
        self.assertTableStruct(
            self.listing_result(''.join(['cluster verification --show ',
                                         cluster_name])), [
                'Field',
                'Value'
            ])

    def openstack_cluster_verification_start(self, cluster_name):
        result = self.openstack('dataprocessing cluster verification --start',
                                params=cluster_name)
        expected_result = VERIF_RESULT % cluster_name
        self.assertEqual(result, expected_result)

    def openstack_cluster_scale(self, cluster_name, ng_worker):
        with fixtures.Timeout(300, gentle=True):
            scale_cluster = self.listing_result(
                ''.join(['cluster scale --instances ', ng_worker,
                         ':2 --wait ', cluster_name]))
            self.assertTableStruct(scale_cluster, [
                'Field',
                'Value'
            ])
        self._poll_cluster_status(cluster_name)
