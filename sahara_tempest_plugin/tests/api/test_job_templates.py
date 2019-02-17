# Copyright (c) 2014 Mirantis Inc.
# Copyright (c) 2018 Red Hat, Inc.
#
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

from testtools import testcase as tc

from tempest import config
from tempest.lib import decorators
from tempest.lib.common.utils import data_utils

from sahara_tempest_plugin.tests.api import base as dp_base


CONF = config.CONF


class JobTemplatesTest(dp_base.BaseDataProcessingTest):
    # NOTE: Link to the API documentation: https://developer.openstack.org/
    # api-ref/data-processing/v2/#job-templates

    @classmethod
    def skip_checks(cls):
        super(JobTemplatesTest, cls).skip_checks()
        if not CONF.data_processing.use_api_v2:
            raise cls.skipException('These tests require API v2')

    @classmethod
    def resource_setup(cls):
        super(JobTemplatesTest, cls).resource_setup()
        # create job binary
        job_binary = {
            'name': data_utils.rand_name('sahara-job-binary'),
            'url': 'swift://sahara-container.sahara/example.jar',
            'description': 'Test job binary',
            'extra': {
                'user': cls.os_primary.credentials.username,
                'password': cls.os_primary.credentials.password
            }
        }
        resp_body = cls.create_job_binary(**job_binary)
        job_binary_id = resp_body['id']

        cls.job = {
            'job_type': 'Pig',
            'mains': [job_binary_id]
        }

    def _create_job_template(self, job_name=None):
        """Creates Job with optional name specified.

        It creates job and ensures job name. Returns id and name of created
        job.
        """
        if not job_name:
            # generate random name if it's not specified
            job_name = data_utils.rand_name('sahara-job')

        # create job
        resp_body = self.create_job_template(job_name, **self.job)

        # ensure that job created successfully
        self.assertEqual(job_name, resp_body['name'])

        return resp_body['id'], job_name

    @decorators.idempotent_id('26e39bc9-df9c-422f-9401-0d2cf5c87c63')
    @tc.attr('smoke')
    def test_job_template_create(self):
        self._create_job_template()

    @decorators.idempotent_id('6d3ce0da-cd37-4ac1-abfa-e53835bd2c08')
    @tc.attr('smoke')
    def test_job_template_list(self):
        job_info = self._create_job_template()

        # check for job in list
        jobs = self.client.list_job_templates()['job_templates']
        jobs_info = [(job['id'], job['name']) for job in jobs]
        self.assertIn(job_info, jobs_info)

    @decorators.idempotent_id('4396453f-f4b2-415c-916c-6929a51ba89f')
    @tc.attr('smoke')
    def test_job_template_get(self):
        job_id, job_name = self._create_job_template()

        # check job fetch by id
        job_t = self.client.get_job_template(job_id)['job_template']

        self.assertEqual(job_name, job_t['name'])

    @decorators.idempotent_id('2d816b08-b20c-438f-8580-3e40fd741eb4')
    @tc.attr('smoke')
    def test_job_template_delete(self):
        job_id, _ = self._create_job_template()

        # delete the job by id
        self.client.delete_job_template(job_id)
        self.wait_for_resource_deletion(job_id, self.client.get_job_template)

        jobs = self.client.list_job_templates()['job_templates']
        jobs_ids = [job['id'] for job in jobs]
        self.assertNotIn(job_id, jobs_ids)
