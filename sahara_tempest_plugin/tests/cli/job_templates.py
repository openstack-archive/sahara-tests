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


class SaharaJobTemplateCLITest(base.ClientTestBase):

    def openstack_job_template_list(self):
        self.assertTableStruct(self.listing_result('job template list'), [
            'Name',
            'Id',
            'Type'
        ])

    def openstack_job_template_create(self, job_binary_name):
        job_template_name = data_utils.rand_name('job-template')
        flag = ("%(name)s %(type)s %(main)s "
                % {'name': ' --name %s' % job_template_name,
                   'type': ' --type Shell',
                   'main': ' --main %s' % job_binary_name})
        self.assertTableStruct(
            self.listing_result('job template create %s' % flag),
            [
                'Field',
                'Value'
            ])
        return job_template_name

    def openstack_job_template_show(self, job_template_name):
        self.find_in_listing(
            self.listing_result('job template show %s' % job_template_name),
            job_template_name)

    def openstack_job_template_update(self, job_template_name):
        self.assertTableStruct(
            self.listing_result('job template update --description '
                                'cli-tests %s' % job_template_name), [
                'Field',
                'Value'
            ])

    def openstack_job_template_delete(self, job_template_name):
        self.check_if_delete('job template', job_template_name)
