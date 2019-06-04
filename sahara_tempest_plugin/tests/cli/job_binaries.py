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

from filecmp import cmp
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

    def openstack_job_binary_create(self, job_internal=True):
        job_binary_name = data_utils.rand_name('job-fake')
        script_name = ''
        if job_internal:
            fd, script_name = tempfile.mkstemp()
            with fdopen(fd, 'w+') as jb:
                jb.write('test-script')
            flag = ("%(jb_name)s %(data)s "
                    % {'jb_name': ('--name %s' % job_binary_name),
                       'data': ' --data %s' % script_name})
        else:
            flag = ("%(jb_name)s --url swift://mybucket.sahara/foo "
                    "--username foo --password bar"
                    % {'jb_name': ('--name %s' % job_binary_name)})
        self.assertTableStruct(
            self.listing_result('job binary create %s' % flag),
            [
                'Field',
                'Value'
            ])
        return job_binary_name, script_name

    def openstack_job_binary_download(self, job_binary_name,
                                      original_file=None):
        if path.exists(job_binary_name):
            remove(job_binary_name)

        self.openstack('dataprocessing job binary download',
                       params=job_binary_name)

        self.assertTrue(path.exists(job_binary_name))
        if original_file:
            self.assertTrue(cmp(job_binary_name, original_file))
            remove(original_file)
        remove(job_binary_name)

    def openstack_job_binary_show(self, job_binary_name):
        self.find_in_listing(self.listing_result('job binary show %s'
                                                 % job_binary_name),
                             job_binary_name)

    def openstack_job_binary_update(self, job_binary_name, flag=None):
        cmd = 'job binary update --%s' % flag
        if flag == 'description':
            self.assertTableStruct(
                self.listing_result('%s cli-tests %s'
                                    % (cmd, job_binary_name)), [
                    'Field',
                    'Value'
                ])
        elif flag == 'name':
            new_job_binary_name = data_utils.rand_name(job_binary_name)
            self.assertTableStruct(
                self.listing_result('%s %s %s'
                                    % (cmd, new_job_binary_name,
                                       job_binary_name)), [
                    'Field',
                    'Value'
                ])
            return new_job_binary_name
        else:
            # here we check only updating with public/protected flags for now
            self.assertTableStruct(
                self.listing_result('%s %s' % (cmd, job_binary_name)), [
                    'Field',
                    'Value'
                ]
            )

    def openstack_job_binary_delete(self, job_binary_name):
        self.openstack('dataprocessing job binary delete',
                       params=job_binary_name)
        list_job_binary = self.listing_result('job binary list')
        for job_binary in list_job_binary:
            if job_binary['Name'] == job_binary_name:
                raise self.skipException('Job binary is not delete')

    def negative_delete_removed_job_binary(self, job_binary_name):
        """Test to remove already deleted job binary"""
        command_to_execute = 'job binary delete'
        self.check_negative_scenarios(base.TEMPEST_ERROR_MESSAGE,
                                      command_to_execute,
                                      job_binary_name)

    def negative_try_to_update_protected_jb(self, job_binary_name):
        """Test to try to update proteted job binary"""
        self.openstack_job_binary_update(job_binary_name, flag='protected')
        error_message = ("JobBinary with id '%s' could not be updated because "
                         "it's marked as protected" %
                         self._get_resource_id('job binary',
                                               job_binary_name))
        command_to_execute = 'job binary update --name test'
        self.check_negative_scenarios(error_message,
                                      command_to_execute,
                                      job_binary_name)

    def filter_job_binaries_in_list(self):
        """Filter job binaries list with --column flag"""
        job_binaries_list = self.listing_result('job binary list '
                                                '--column Name')
        self.assertTableStruct(job_binaries_list, ['Name'])
