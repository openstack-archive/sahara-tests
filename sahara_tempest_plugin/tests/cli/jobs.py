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

DELETE_RES = '''\
job "%s" deletion has been started.
'''


class SaharaJobCLITest(base.ClientTestBase):

    def openstack_job_list(self):
        self.assertTableStruct(self.listing_result('job list'), [
            'Id',
            'Cluster id',
            'Job id',
            'Status'
        ])

    def openstack_job_execute(self, cluster_name, job_template_name, input,
                              output):
        flag = ("%(cluster)s %(jt)s %(input)s %(output)s"
                % {'cluster': ' --cluster %s' % cluster_name,
                   'jt': ' --job-template %s' % job_template_name,
                   'input': ' --input %s' % input,
                   'output': ' --output %s' % output})
        result = self.listing_result('job execute %s' % flag)
        self.assertTableStruct(
            result,
            [
                'Field',
                'Value'
            ])
        for line in result:
            if line['Field'] == 'Id':
                return line['Value']

    def openstack_job_show(self, job_id):
        result = self.listing_result('job show %s' % job_id)
        check_table = False
        for line in result:
            if line['Field'] == 'Id':
                self.assertEqual(line['Value'], job_id)
                check_table = True
        if not check_table:
            raise self.skipException('No table to show information')

    def openstack_job_update(self, job_id):
        self.assertTableStruct(
            self.listing_result(
                'job update --public %s' % job_id), [
                'Field',
                'Value'
            ])

    def openstack_job_delete(self, job_id):
        delete_job = self.openstack('dataprocessing job delete',
                                    params=job_id)
        self.assertEqual(delete_job.lower(), DELETE_RES % job_id)
