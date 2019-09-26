#!/bin/bash
#
# Copyright (c) 2015 Mirantis Inc.
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

# This script is executed inside post_test_hook function in devstack gate.

set -ex

source commons $@

set +x
source $DEVSTACK_DIR/stackrc
source $DEVSTACK_DIR/openrc admin admin
set -x

# Make public and register in Sahara as admin
sahara_register_image

# Register sahara specific flavor for gate
sahara_register_flavor

sudo -E chown -R $USER:stack $SAHARA_TESTS_DIR
cd $SAHARA_TESTS_DIR

echo "Generating scenario tests config file"
sudo -E -u $USER tee template_vars.ini <<EOF
[DEFAULT]
network_private_name: ${PRIVATE_NETWORK_NAME}
network_public_name: ${PUBLIC_NETWORK_NAME}
plugin_image: ${SAHARA_IMAGE_NAME}
ci_flavor_id: '${SAHARA_FLAVOR_ID}'
cluster_name: fake-cluster
is_transient: ${IS_TRANSIENT}
auto_security_group: ${AUTO_SECURITY_GROUP}
EOF

echo "Running scenario tests"
# TODO(slukjanov): Create separated list of templates for fake plugin in gate
sudo -u $USER tox -e venv -- sahara-scenario --verbose -V template_vars.ini \
    etc/scenario/gate/credentials.yaml.mako \
    etc/scenario/gate/edp.yaml.mako \
    etc/scenario/gate/$SAHARA_SCENARIO_TEMPLATE \
    --os-cloud devstack \
    | tee scenario.log

if grep -q FAILED scenario.log; then
    exit 1
fi
