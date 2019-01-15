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

from tempest.lib import decorators
from tempest.lib.common.utils import data_utils

from sahara_tempest_plugin.tests.api import base as dp_base


class NodeGroupTemplateTest(dp_base.BaseDataProcessingTest):

    @classmethod
    def skip_checks(cls):
        super(NodeGroupTemplateTest, cls).skip_checks()
        if cls.default_plugin is None:
            raise cls.skipException("No Sahara plugins configured")

    @classmethod
    def resource_setup(cls):
        super(NodeGroupTemplateTest, cls).resource_setup()

    def _create_node_group_template(self, template_name=None):
        """Creates Node Group Template with optional name specified.

        It creates template, ensures template name and response body.
        Returns id and name of created template.
        """
        self.node_group_template = self.get_node_group_template()
        self.assertIsNotNone(self.node_group_template,
                             "No known Sahara plugin was found")

        if not template_name:
            # generate random name if it's not specified
            template_name = data_utils.rand_name('sahara-ng-template')

        # hack the arguments: keep the compatibility with the signature
        # of self.create_node_group_template
        node_group_template_w = self.node_group_template.copy()
        if 'plugin_version' in node_group_template_w:
            plugin_version_value = node_group_template_w['plugin_version']
            del node_group_template_w['plugin_version']
            node_group_template_w['hadoop_version'] = plugin_version_value

        # create node group template
        resp_body = self.create_node_group_template(template_name,
                                                    **node_group_template_w)

        # ensure that template created successfully
        self.assertEqual(template_name, resp_body['name'])
        self.assertDictContainsSubset(self.node_group_template, resp_body)

        return resp_body['id'], template_name

    @tc.attr('smoke')
    @decorators.idempotent_id('63164051-e46d-4387-9741-302ef4791cbd')
    def test_node_group_template_create(self):
        self._create_node_group_template()

    @tc.attr('smoke')
    @decorators.idempotent_id('eb39801d-2612-45e5-88b1-b5d70b329185')
    def test_node_group_template_list(self):
        template_info = self._create_node_group_template()

        # check for node group template in list
        templates = self.client.list_node_group_templates()
        templates = templates['node_group_templates']
        templates_info = [(template['id'], template['name'])
                          for template in templates]
        self.assertIn(template_info, templates_info)

    @tc.attr('smoke')
    @decorators.idempotent_id('6ee31539-a708-466f-9c26-4093ce09a836')
    def test_node_group_template_get(self):
        template_id, template_name = self._create_node_group_template()

        # check node group template fetch by id
        template = self.client.get_node_group_template(template_id)
        template = template['node_group_template']
        self.assertEqual(template_name, template['name'])
        self.assertDictContainsSubset(self.node_group_template, template)

    @tc.attr('smoke')
    @decorators.idempotent_id('f4f5cb82-708d-4031-81c4-b0618a706a2f')
    def test_node_group_template_delete(self):
        template_id, _ = self._create_node_group_template()

        # delete the node group template by id
        self.client.delete_node_group_template(template_id)
        get_resource = self.client.get_node_group_template
        self.wait_for_resource_deletion(template_id, get_resource)

        templates = self.client.list_node_group_templates()
        templates = templates['node_group_templates']
        templates_ids = [template['id'] for template in templates]
        self.assertNotIn(template_id, templates_ids)

    @tc.attr('smoke')
    @decorators.idempotent_id('b048b603-832f-4ca5-9d5f-7a0e042f16b5')
    def test_node_group_template_update(self):
        template_id, template_name = self._create_node_group_template()

        new_template_name = 'updated-template-name'
        body = {'name': new_template_name}
        updated_template = self.client.update_node_group_template(template_id,
                                                                  **body)
        updated_template = updated_template['node_group_template']

        self.assertEqual(new_template_name, updated_template['name'])
