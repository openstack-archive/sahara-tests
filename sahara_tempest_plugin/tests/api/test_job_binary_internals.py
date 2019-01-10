# Copyright (c) 2014 Mirantis Inc.
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


class JobBinaryInternalTest(dp_base.BaseDataProcessingTest):
    # Link to the API documentation is https://developer.openstack.org/
    # api-ref/data-processing/#job-binary-internals

    @classmethod
    def skip_checks(cls):
        super(JobBinaryInternalTest, cls).skip_checks()
        if CONF.data_processing.use_api_v2:
            raise cls.skipException('Job binaries stored on the internal db '
                                    'are available only with API v1.1')

    @classmethod
    def resource_setup(cls):
        super(JobBinaryInternalTest, cls).resource_setup()
        cls.job_binary_internal_data = 'Some script may be data'

    def _create_job_binary_internal(self, binary_name=None):
        """Creates Job Binary Internal with optional name specified.

        It puts data into Sahara database and ensures job binary internal name.
        Returns id and name of created job binary internal.
        """
        if not binary_name:
            # generate random name if it's not specified
            binary_name = data_utils.rand_name('sahara-job-binary-internal')

        # create job binary internal
        resp_body = (
            self.create_job_binary_internal(binary_name,
                                            self.job_binary_internal_data))

        # ensure that job binary internal created successfully
        self.assertEqual(binary_name, resp_body['name'])

        return resp_body['id'], binary_name

    @tc.attr('smoke')
    @decorators.idempotent_id('249c4dc2-946f-4939-83e6-212ddb6ea0be')
    def test_job_binary_internal_create(self):
        self._create_job_binary_internal()

    @tc.attr('smoke')
    @decorators.idempotent_id('1e3c2ecd-5673-499d-babe-4fe2fcdf64ee')
    def test_job_binary_internal_list(self):
        binary_info = self._create_job_binary_internal()

        # check for job binary internal in list
        binaries = self.client.list_job_binary_internals()['binaries']
        binaries_info = [(binary['id'], binary['name']) for binary in binaries]
        self.assertIn(binary_info, binaries_info)

    @tc.attr('smoke')
    @decorators.idempotent_id('a2046a53-386c-43ab-be35-df54b19db776')
    def test_job_binary_internal_get(self):
        binary_id, binary_name = self._create_job_binary_internal()

        # check job binary internal fetch by id
        binary = self.client.get_job_binary_internal(binary_id)
        self.assertEqual(binary_name, binary['job_binary_internal']['name'])

    @tc.attr('smoke')
    @decorators.idempotent_id('b3568c33-4eed-40d5-aae4-6ff3b2ac58f5')
    def test_job_binary_internal_delete(self):
        binary_id, _ = self._create_job_binary_internal()

        # delete the job binary internal by id
        self.client.delete_job_binary_internal(binary_id)
        get_resource = self.client.get_job_binary_internal
        self.wait_for_resource_deletion(binary_id, get_resource)

        # check for job binary internal in list
        binaries = self.client.list_job_binary_internals()['binaries']
        binaries_ids = [binary['id'] for binary in binaries]
        self.assertNotIn(binary_id, binaries_ids)

    @tc.attr('smoke')
    @decorators.idempotent_id('8871f2b0-5782-4d66-9bb9-6f95bcb839ea')
    def test_job_binary_internal_get_data(self):
        binary_id, _ = self._create_job_binary_internal()

        # get data of job binary internal by id
        _, data = self.client.get_job_binary_internal_data(binary_id)
        self.assertEqual(data.decode("utf-8"), self.job_binary_internal_data)
