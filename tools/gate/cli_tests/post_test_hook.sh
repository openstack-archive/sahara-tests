#!/bin/bash -xe

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# This script is executed inside post_test_hook function in devstack gate.

source commons $@

export DEST=${DEST:-$BASE/new}
export DEVSTACK_DIR=${DEVSTACK_DIR:-$DEST/devstack}
export SAHARA_TESTS_DIR="$BASE/new/sahara-tests"

# Get admin credentials
set +x
source $DEVSTACK_DIR/stackrc
source $DEVSTACK_DIR/openrc admin admin
set -x

# Prepare image for Sahara
sahara_prepare_fake_plugin_image

# Register sahara specific flavor for gate
sahara_register_flavor

# Go to the sahara-tests dir
sudo chown -R jenkins:stack $SAHARA_TESTS_DIR

cd $SAHARA_TESTS_DIR

# Run sahara cli tests
echo "Running sahara cli test suite"
sudo -E -H -u jenkins tox -e cli-tests
