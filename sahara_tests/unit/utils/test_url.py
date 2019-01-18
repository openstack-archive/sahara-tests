# Copyright 2018 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import testtools

from sahara_tests.utils import url as utils_url


class UrlUnitTest(testtools.TestCase):

    def _check_clean_url(self, url, expected_clean_url):
        """Check if the cleaned URL matches the expected one."""
        clean_url = utils_url.url_schema_remover(url)
        self.assertEqual(clean_url, expected_clean_url)

    def test_clean_url_http(self):
        self._check_clean_url('https://s3.amazonaws.com',
                              's3.amazonaws.com')

    def test_clean_url_https_longer(self):
        self._check_clean_url('https://s3.amazonaws.com/foo',
                              's3.amazonaws.com/foo')

    def test_clean_url_file(self):
        self._check_clean_url('file:///s3.amazonaws.com/bar',
                              '/s3.amazonaws.com/bar')
