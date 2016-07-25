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

from os import fdopen
from os import path
from os import remove
import tempfile

from tempest.lib.common.utils import data_utils

from sahara_tempest_plugin.tests.cli import base


class SaharaJobBinaryCLITest(base.ClientTestBase):

    def openstack_job_binary_list(self):
        self.assertTableStruct(self.listing_result('job binary list'), [
            'Name',
            'Id',
            'Url'
        ])

    def openstack_job_binary_create(self):
        fd, script_name = tempfile.mkstemp()
        with fdopen(fd, 'w+') as jb:
            jb.write('test-script')
        job_binary_name = data_utils.rand_name('job-fake')
        flag = ("%(jb_name)s %(data)s "
                % {'jb_name': ('--name %s' % job_binary_name),
                   'data': ' --data %s' % script_name})
        self.assertTableStruct(
            self.listing_result('job binary create %s' % flag),
            [
                'Field',
                'Value'
            ])
        remove(script_name)
        return job_binary_name

    def openstack_job_binary_download(self, job_binary_name):
        self.openstack('dataprocessing job binary download ',
                       params=job_binary_name)
        self.assertTrue(path.exists(job_binary_name))

    def openstack_job_binary_show(self, job_binary_name):
        self.find_in_listing(self.listing_result('job binary show %s'
                                                 % job_binary_name),
                             job_binary_name)

    def openstack_job_binary_update(self, job_binary_name):
        self.assertTableStruct(
            self.listing_result('job binary update --description cli-tests '
                                '% s' % job_binary_name), [
                'Field',
                'Value'
            ])

    def openstack_job_binary_delete(self, job_binary_name):
        self.openstack('dataprocessing job binary delete',
                       params=job_binary_name)
        list_job_binary = self.listing_result('job binary list')
        for job_binary in list_job_binary:
            if job_binary['Name'] == job_binary_name:
                raise self.skipException('Job binary is not delete')
