#!/bin/bash

set -ex

source commons $@

echo "IMAGE_URLS=$SAHARA_FAKE_PLUGIN_IMAGE" >> $LOCALRC_PATH
