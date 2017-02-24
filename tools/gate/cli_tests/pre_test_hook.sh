#!/bin/bash

set -ex

source commons $@

echo "[[local|localrc]]" >> $LOCALCONF_PATH
echo "IMAGE_URLS=$SAHARA_FAKE_PLUGIN_IMAGE" >> $LOCALCONF_PATH
