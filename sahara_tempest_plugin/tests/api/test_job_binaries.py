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

import testtools
from testtools import testcase as tc

from tempest import config
from tempest.lib import decorators
from tempest.lib.common.utils import data_utils

from sahara_tempest_plugin.tests.api import base as dp_base


CONF = config.CONF


class JobBinaryTest(dp_base.BaseDataProcessingTest):
    # Link to the API documentation is https://developer.openstack.org/
    # api-ref/data-processing/#job-binaries

    @classmethod
    def resource_setup(cls):
        super(JobBinaryTest, cls).resource_setup()
        cls.swift_job_binary_with_extra = {
            'url': 'swift://sahara-container.sahara/example.jar',
            'description': 'Test job binary',
            'extra': {
                'user': cls.os_primary.credentials.username,
                'password': cls.os_primary.credentials.password
            }
        }
        cls.s3_job_binary_with_extra = {
            'url': 's3://sahara-bucket/example.jar',
            'description': 'Test job binary',
            'extra': {
                'accesskey': cls.os_primary.credentials.username,
                'secretkey': cls.os_primary.credentials.password,
                'endpoint': 'localhost'
            }
        }
        # Create extra cls.swift_job_binary and cls.s3_job_binary variables
        # to use for comparison to job binary response body
        # because response body has no 'extra' field.
        cls.swift_job_binary = cls.swift_job_binary_with_extra.copy()
        del cls.swift_job_binary['extra']
        cls.s3_job_binary = cls.s3_job_binary_with_extra.copy()
        del cls.s3_job_binary['extra']

        name = data_utils.rand_name('sahara-internal-job-binary')
        cls.job_binary_data = 'Some script may be data'
        if not CONF.data_processing.use_api_v2:
            job_binary_internal = (
                cls.create_job_binary_internal(name, cls.job_binary_data))
            cls.internal_db_job_binary = {
                'url': 'internal-db://%s' % job_binary_internal['id'],
                'description': 'Test job binary',
            }

    def _create_job_binary(self, binary_body, binary_name=None):
        """Creates Job Binary with optional name specified.

        It creates a link to data (jar, pig files, etc.), ensures job binary
        name and response body. Returns id and name of created job binary.
        Data may not exist when using Swift or S3 as data storage.
        In other cases data must exist in storage.
        """
        if not binary_name:
            # generate random name if it's not specified
            binary_name = data_utils.rand_name('sahara-job-binary')

        # create job binary
        resp_body = self.create_job_binary(binary_name, **binary_body)

        # ensure that binary created successfully
        self.assertEqual(binary_name, resp_body['name'])
        if binary_body['url'].startswith('swift:'):
            binary_body = self.swift_job_binary
        elif binary_body['url'].startswith('s3:'):
            binary_body = self.s3_job_binary
        self.assertDictContainsSubset(binary_body, resp_body)

        return resp_body['id'], binary_name

    @tc.attr('smoke')
    @decorators.idempotent_id('c00d43f8-4360-45f8-b280-af1a201b12d3')
    def test_swift_job_binary_create(self):
        self._create_job_binary(self.swift_job_binary_with_extra)

    @tc.attr('smoke')
    @decorators.idempotent_id('f8809352-e79d-4748-9359-ce1efce89f2a')
    def test_swift_job_binary_list(self):
        binary_info = self._create_job_binary(self.swift_job_binary_with_extra)

        # check for job binary in list
        binaries = self.client.list_job_binaries()['binaries']
        binaries_info = [(binary['id'], binary['name']) for binary in binaries]
        self.assertIn(binary_info, binaries_info)

    @tc.attr('smoke')
    @decorators.idempotent_id('2d4a670f-e8f1-413c-b5ac-50c1bfe9e1b1')
    def test_swift_job_binary_get(self):
        binary_id, binary_name = (
            self._create_job_binary(self.swift_job_binary_with_extra))

        # check job binary fetch by id
        binary = self.client.get_job_binary(binary_id)['job_binary']
        self.assertEqual(binary_name, binary['name'])
        self.assertDictContainsSubset(self.swift_job_binary, binary)

    @tc.attr('smoke')
    @decorators.idempotent_id('9b0e8f38-04f3-4616-b399-cfa7eb2677ed')
    def test_swift_job_binary_delete(self):
        binary_id, _ = (
            self._create_job_binary(self.swift_job_binary_with_extra))

        # delete the job binary by id
        self.client.delete_job_binary(binary_id)

    @decorators.idempotent_id('1cda1990-bfa1-46b1-892d-fc3ceafde537')
    @testtools.skipUnless(CONF.data_processing_feature_enabled.s3,
                          'S3 not available')
    def test_s3_job_binary_create(self):
        self._create_job_binary(self.s3_job_binary_with_extra)

    @decorators.idempotent_id('69de4774-44fb-401d-9d81-8c4df83d6cdb')
    @testtools.skipUnless(CONF.data_processing_feature_enabled.s3,
                          'S3 not available')
    def test_s3_job_binary_list(self):
        binary_info = self._create_job_binary(self.s3_job_binary_with_extra)

        # check for job binary in list
        binaries = self.client.list_job_binaries()['binaries']
        binaries_info = [(binary['id'], binary['name']) for binary in binaries]
        self.assertIn(binary_info, binaries_info)

    @decorators.idempotent_id('479ba3ef-67b7-45c9-81e2-ea34366099ce')
    @testtools.skipUnless(CONF.data_processing_feature_enabled.s3,
                          'S3 not available')
    def test_s3_job_binary_get(self):
        binary_id, binary_name = (
            self._create_job_binary(self.s3_job_binary_with_extra))

        # check job binary fetch by id
        binary = self.client.get_job_binary(binary_id)['job_binary']
        self.assertEqual(binary_name, binary['name'])
        self.assertDictContainsSubset(self.s3_job_binary, binary)

    @decorators.idempotent_id('d949472b-6a57-4250-905d-087dfb614633')
    @testtools.skipUnless(CONF.data_processing_feature_enabled.s3,
                          'S3 not available')
    def test_s3_job_binary_delete(self):
        binary_id, _ = (
            self._create_job_binary(self.s3_job_binary_with_extra))

        # delete the job binary by id
        self.client.delete_job_binary(binary_id)

    @tc.attr('smoke')
    @decorators.idempotent_id('63662f6d-8291-407e-a6fc-f654522ebab6')
    @testtools.skipIf(CONF.data_processing.api_version_saharaclient != '1.1',
                      'Job binaries stored on the internal db are available '
                      'only with API v1.1')
    def test_internal_db_job_binary_create(self):
        self._create_job_binary(self.internal_db_job_binary)

    @tc.attr('smoke')
    @decorators.idempotent_id('38731e7b-6d9d-4ffa-8fd1-193c453e88b1')
    @testtools.skipIf(CONF.data_processing.api_version_saharaclient != '1.1',
                      'Job binaries stored on the internal db are available '
                      'only with API v1.1')
    def test_internal_db_job_binary_list(self):
        binary_info = self._create_job_binary(self.internal_db_job_binary)

        # check for job binary in list
        binaries = self.client.list_job_binaries()['binaries']
        binaries_info = [(binary['id'], binary['name']) for binary in binaries]
        self.assertIn(binary_info, binaries_info)

    @tc.attr('smoke')
    @decorators.idempotent_id('1b32199b-c3f5-43e1-a37a-3797e57b7066')
    @testtools.skipIf(CONF.data_processing.api_version_saharaclient != '1.1',
                      'Job binaries stored on the internal db are available '
                      'only with API v1.1')
    def test_internal_db_job_binary_get(self):
        binary_id, binary_name = (
            self._create_job_binary(self.internal_db_job_binary))

        # check job binary fetch by id
        binary = self.client.get_job_binary(binary_id)['job_binary']
        self.assertEqual(binary_name, binary['name'])
        self.assertDictContainsSubset(self.internal_db_job_binary, binary)

    @tc.attr('smoke')
    @decorators.idempotent_id('3c42b0c3-3e03-46a5-adf0-df0650271a4e')
    @testtools.skipIf(CONF.data_processing.api_version_saharaclient != '1.1',
                      'Job binaries stored on the internal db are available '
                      'only with API v1.1')
    def test_internal_db_job_binary_delete(self):
        binary_id, _ = self._create_job_binary(self.internal_db_job_binary)

        # delete the job binary by id
        self.client.delete_job_binary(binary_id)
        self.wait_for_resource_deletion(binary_id, self.client.get_job_binary)

        binaries = self.client.list_job_binaries()['binaries']
        binaries_ids = [binary['id'] for binary in binaries]
        self.assertNotIn(binary_id, binaries_ids)

    @tc.attr('smoke')
    @decorators.idempotent_id('d5d47659-7e2c-4ea7-b292-5b3e559e8587')
    @testtools.skipIf(CONF.data_processing.api_version_saharaclient != '1.1',
                      'Job binaries stored on the internal db are available '
                      'only with API v1.1')
    def test_job_binary_get_data(self):
        binary_id, _ = self._create_job_binary(self.internal_db_job_binary)

        # get data of job binary by id
        _, data = self.client.get_job_binary_data(binary_id)
        self.assertEqual(data.decode("utf-8"), self.job_binary_data)
