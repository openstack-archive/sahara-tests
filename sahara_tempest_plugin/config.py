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


data_processing_feature_group = cfg.OptGroup(
    name="data-processing-feature-enabled",
    title="Enabled Data Processing features")

DataProcessingFeaturesGroup = [
    cfg.ListOpt('plugins',
                default=["vanilla", "cdh"],
                help="List of enabled data processing plugins")
]
