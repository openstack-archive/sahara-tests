# Copyright (c) 2013 Mirantis Inc.
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

from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client


class BaseDataProcessingClient(rest_client.RestClient):

    def _request_and_check_resp(self, request_func, uri, resp_status):
        """Make a request and check response status code.

        It returns a ResponseBody.
        """
        resp, body = request_func(uri)
        self.expected_success(resp_status, resp.status)
        return rest_client.ResponseBody(resp, body)

    def _request_and_check_resp_data(self, request_func, uri, resp_status):
        """Make a request and check response status code.

        It returns pair: resp and response data.
        """
        resp, body = request_func(uri)
        self.expected_success(resp_status, resp.status)
        return resp, body

    def _request_check_and_parse_resp(self, request_func, uri,
                                      resp_status, *args, **kwargs):
        """Make a request, check response status code and parse response body.

        It returns a ResponseBody.
        """
        headers = {'Content-Type': 'application/json'}
        resp, body = request_func(uri, headers=headers, *args, **kwargs)
        self.expected_success(resp_status, resp.status)
        body = json.loads(body)
        return rest_client.ResponseBody(resp, body)
