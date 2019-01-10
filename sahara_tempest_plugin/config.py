# Copyright 2016 Red Hat, Inc.
# All Rights Reserved.
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

from oslo_config import cfg

service_option = cfg.BoolOpt("sahara",
                             default=False,
                             help="Whether or not sahara is expected to be "
                                  "available")

data_processing_group = cfg.OptGroup(name="data-processing",
                                     title="Data Processing options")

DataProcessingGroup = [
    cfg.StrOpt('catalog_type',
               default='data-processing',
               help="Catalog type of the data processing service."),
    cfg.StrOpt('endpoint_type',
               default='publicURL',
               choices=['public', 'admin', 'internal',
                        'publicURL', 'adminURL', 'internalURL'],
               help="The endpoint type to use for the data processing "
                    "service."),
]

DataProcessingAdditionalGroup = [
    cfg.IntOpt('cluster_timeout',
               default=3600,
               help='Timeout (in seconds) to wait for cluster deployment.'),
    cfg.IntOpt('request_timeout',
               default=10,
               help='Timeout (in seconds) between status checks.'),
    # FIXME: the default values here are an hack needed until it is possible
    # to pass values from the job to tempest.conf (or a devstack plugin is
    # written).
    cfg.StrOpt('test_image_name',
               default='xenial-server-cloudimg-amd64-disk1',
               help='name of an image which is used for cluster creation.'),
    cfg.StrOpt('test_ssh_user',
               default='ubuntu',
               help='username used to access the test image.'),
    cfg.BoolOpt('use_api_v2',
                default=False,
                help='Run API tests against APIv2 instead of 1.1'),
    cfg.StrOpt('api_version_saharaclient',
               default='1.1',
               help='Version of Sahara API used by saharaclient',
               deprecated_name='saharaclient_version'),
    cfg.StrOpt('sahara_url',
               help='Sahara url as http://ip:port/api_version/tenant_id'),
    # TODO(shuyingya): Delete this option once the Mitaka release is EOL.
    cfg.BoolOpt('plugin_update_support',
                default=True,
                help='Does sahara support plugin update?'),
]


data_processing_feature_group = cfg.OptGroup(
    name="data-processing-feature-enabled",
    title="Enabled Data Processing features")

DataProcessingFeaturesGroup = [
    cfg.ListOpt('plugins',
                default=["vanilla", "cdh"],
                help="List of enabled data processing plugins"),
    # delete this and always execute the tests when Tempest and
    # this Tempest plugin stop supporting Queens, the last version
    # without or incomplete S3 support.
    cfg.BoolOpt('s3',
                default=False,
                help='Does Sahara support S3?'),
]
