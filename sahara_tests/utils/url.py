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

from six.moves.urllib import parse as urlparse


def url_schema_remover(url):
    """ Return the same URL without the schema.
    Example: prefix://host/path -> host/path
    """
    parsed = urlparse.urlsplit(url)
    cleaned = urlparse.urlunsplit((('',) + parsed[1:]))
    if cleaned.startswith('//'):
        cleaned = cleaned[2:]
    return cleaned
