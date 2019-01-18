System(scenario) tests for Sahara project
=========================================

_`Authentication`
-----------------

You need to be authenticated to run these tests. To authenticate you should
create openrc file (like in devstack) and source it.

.. sourcecode:: bash

     #!/bin/sh
     export OS_TENANT_NAME='admin'
     export OS_PROJECT_NAME='admin'
     export OS_USERNAME='admin'
     export OS_PASSWORD='admin'
     export OS_AUTH_URL='http://localhost:5000/v2.0'

..

Also you can specify the authentication details for Sahara tests using flags
in run-command:

.. sourcecode:: console

   List of flags:
     --os-username
     --os-password
     --os-project-name
     --os-auth-url
..

Last way to set the authentication details for these tests is using a
``clouds.yaml`` file.

After creating the file, you can set ``OS_CLOUD`` variable or ``--os-cloud``
flag to the name of the cloud you have created and those values will be used.

We have an example of a ``clouds.yaml`` file, and you can find it in
``sahara_tests/unit/scenario/clouds.yaml``.

Using this example, you can create your own file with clouds instead of
setting the ``OS_CLOUD`` variable or the ``--os-cloud`` flag. Note that more
than one cloud can be defined in the same file.

Here you can find more information about
`clouds
<https://docs.openstack.org/os-client-config/latest/user/configuration.html#config-files>`_

Template variables
------------------
You need to define these variables because they are used in mako template
files and replace the values from scenario files. These names pass to the test
runner through the ``-V`` parameter and a special config file.

The format of the config file is an INI-style file, as accepted by the Python
ConfigParser module. The key/values must be specified in the DEFAULT section.

Variables and defaults templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The following variables are currently used by defaults templates:

+-----------------------------+--------+-------------------------+
|   Variable                  |  Type  |          Value          |
+=============================+========+=========================+
| network_type                | string | neutron or nova-network |
+-----------------------------+--------+-------------------------+
| network_private_name        | string | private network name    |
|                             |        | for OS_PROJECT_NAME     |
+-----------------------------+--------+-------------------------+
| network_public_name         | string | public network name     |
+-----------------------------+--------+-------------------------+
| <plugin_name_version>_image | string | name of the image to be |
|                             |        | used for the specific   |
|                             |        | plugin/version          |
+-----------------------------+--------+-------------------------+
| {ci,medium,large}_flavor_id | string | IDs of flavor with      |
|                             |        | different size          |
+-----------------------------+--------+-------------------------+

After finishing with authentication and configuration of file with template
variables, you can run Sahara tests using Sahara Scenario Framework.

How to run
----------

Scenario framework has default templates for testing Sahara. To
use them, specify plugin and version (for transient check and fake plugin,
version is not necessary):

.. sourcecode:: console

    $ tox -e venv -- sahara-scenario -p vanilla -v 2.7.1
..

Different OpenStack releases may require different configuration for the
same set of plugin and versions. If you use the plugin and version flag,
if you want to use the configuration file for a specific OpenStack release
supported by sahara-scenario, you can specify also the ``-r RELEASE``
argument, where ``RELEASE`` is the official name of the OpenStack release.

By default only default configuration files for the specified plugin and
version (and release, if any) are included. Also, if any job configuration
is included, only jobs not tagged with any features will be executed.
In order to enable feature-specific configuration settings, pass
the list of requested features through the ``--feature`` (``-f``) parameter.

The parameter makes sure that:

* additional base configuration file which are feature-specific are included;
* in addition to non-tagged jobs, jobs which are tagged with the specified
  features are included too.

Example:

.. sourcecode:: console

    $ tox -e venv -- sahara-scenario -p vanilla -v 2.7.1 -f s3 -f myfeature -r rocky
..

Create the YAML and/or the YAML mako template files for scenario tests
``etc/scenario/simple-testcase.yaml``.
You can take a look at sample YAML files `How to write scenario files`_.

The file ``templatevars.ini`` contains the values of the variables referenced
by any testcase you are going to run.

If you want to run tests for the Vanilla plugin with the Hadoop version 2.7.1,
you should create ``templatevars.ini`` with the appropriate values (see the
section `Variables and defaults templates`_) and use the following tox env:

.. sourcecode:: console

    $ tox -e venv -- sahara-scenario -V templatevars.ini sahara_tests/scenario/defaults/vanilla-2.7.1.yaml.mako
..

Credentials locate in ``sahara_tests/scenario/defaults/credentials.yaml.mako``.
This file replace the variables included into testcase YAML or YAML Mako files
with the values defined into ``templatevars.ini``.

.. sourcecode:: console

    $ tox -e venv -- sahara-scenario -V templatevars.ini sahara_tests/scenario/defaults/credentials.yaml.mako sahara_tests/scenario/defaults/vanilla-2.7.1.yaml.mako

..

The most useful and comfortable way to run sahara-scenario tests for Vanilla
Plugin:

.. sourcecode:: console

    $ tox -e venv -- sahara-scenario -V templatevars.ini sahara_tests/scenario/defaults/credantials.yaml.mako -p vanilla -v 2.7.1

..

For more information about writing scenario YAML files, see the section
section `How to write scenario files`_.

Virtual environment flags
-------------------------

You can use the following flags to the Sahara scenario tests.

Optional arguments
~~~~~~~~~~~~~~~~~~

+-------------------+----------------------------+
|   Arguments       |   Description              |
+===================+============================+
| --help, -h        | show help message and exit |
+-------------------+----------------------------+
| --variable_file,  | path to the file with      |
| -V                | template variables         |
+-------------------+----------------------------+
| --verbose         | increase output verbosity  |
+-------------------+----------------------------+
| --validate        | validate yaml-files,       |
|                   | tests will not be run      |
+-------------------+----------------------------+
| --args ARGS       | pairs of argument          |
|                   | key:value                  |
+-------------------+----------------------------+
| --plugin,         | specify plugin name        |
| -p PLUGIN         |                            |
+-------------------+----------------------------+
| --plugin_version, | specify plugin version     |
| -v PLUGIN_VERSION |                            |
+-------------------+----------------------------+
| --release,        | specify Sahara release     |
| -r RELEASE        |                            |
+-------------------+----------------------------+
| --report          | write results to file      |
+-------------------+----------------------------+
| --feature,        | list of features           |
| -f FEAT1          | that should be enabled     |
| [-f FEAT2 ...]    |                            |
+-------------------+----------------------------+
| --count COUNT     | specify count of runs      |
+-------------------+----------------------------+
| --os-cloud name   | name of cloud to connect   |
+-------------------+----------------------------+
| --os-auth-type,   |                            |
| --os-auth-plugin  | authentication type to use |
| name              |                            |
+-------------------+----------------------------+

Authentication options
~~~~~~~~~~~~~~~~~~~~~~

Options specific to the password plugin.

+--------------------------+--------------------------------+
|   Arguments              |   Description                  |
+==========================+================================+
| --os-auth-url            | authentication URL             |
| OS_AUTH_URL              |                                |
+--------------------------+--------------------------------+
| --os-domain-id           | domain ID to scope to          |
| OS_DOMAIN_ID             |                                |
+--------------------------+--------------------------------+
| --os-domain-name         | domain name to scope to        |
| OS_DOMAIN_NAME           |                                |
+--------------------------+--------------------------------+
| --os-project-id          |                                |
| --os-tenant-id           | project ID to scope to         |
| OS_PROJECT_ID            |                                |
+--------------------------+--------------------------------+
| --os-project-name        |                                |
| --os-tenant-name         | project name to scope to       |
| OS_PROJECT_NAME          |                                |
+--------------------------+--------------------------------+
| --os-project-domain-id   | domain ID containing project   |
| OS_PROJECT_DOMAIN_ID     |                                |
+--------------------------+--------------------------------+
| --os-project-domain-name | domain name containing project |
| OS_PROJECT_DOMAIN_NAME   |                                |
+--------------------------+--------------------------------+
| --os-trust-id            | trust ID                       |
| OS_TRUST_ID              |                                |
+--------------------------+--------------------------------+
|                          | optional domain ID to use with |
|                          | v3 and v2 parameters. It will  |
| --os-default-domain-id   | be used for both the user and  |
| OS_DEFAULT_DOMAIN_ID     | project domain in v3 and       |
|                          | ignored in v2 authentication.  |
+--------------------------+--------------------------------+
|                          | optional domain name to use    |
|                          | with v3 API and v2parameters.  |
| --os-default-domain-name | It will be used for both       |
| OS_DEFAULT_DOMAIN_NAME   | the user and project domain    |
|                          | in v3 and ignored in v2        |
|                          | authentication.                |
+--------------------------+--------------------------------+
| --os-user-id             | user ID                        |
| OS_USER_ID               |                                |
+--------------------------+--------------------------------+
| --os-username,           |                                |
| --os-user-name           | username                       |
| OS_USERNAME              |                                |
+--------------------------+--------------------------------+
| --os-user-domain-id      | user's domain id               |
| OS_USER_DOMAIN_ID        |                                |
+--------------------------+--------------------------------+
| --os-user-domain-name    | user's domain name             |
| OS_USER_DOMAIN_NAME      |                                |
+--------------------------+--------------------------------+
| --os-password            | user's password                |
| OS_PASSWORD              |                                |
+--------------------------+--------------------------------+

API Connection Options
~~~~~~~~~~~~~~~~~~~~~~

Options controlling the HTTP API connections.

+--------------------------+--------------------------------------+
|   Arguments              |   Description                        |
+==========================+======================================+
|                          | explicitly allow client to           |
|                          | perform "insecure" TLS (https)       |
| --insecure               | requests. The server's               |
|                          | certificate will not be verified     |
|                          | against any certificate authorities. |
|                          | This option should be used with      |
|                          | caution.                             |
+--------------------------+--------------------------------------+
|                          | specify a CA bundle file to use in   |
| --os-cacert              | verifying a TLS(https) server        |
| <ca-certificate>         | certificate. Defaults to env         |
|                          | [OS_CACERT].                         |
+--------------------------+--------------------------------------+
| --os-cert <certificate>  | defaults to env[OS_CERT]             |
+--------------------------+--------------------------------------+
| --os-key <key>           | defaults to env[OS_KEY]              |
+--------------------------+--------------------------------------+
| --timeout <seconds>      | set request timeout (in seconds)     |
+--------------------------+--------------------------------------+

Service Options
~~~~~~~~~~~~~~~

Options control the specialization of the API connection from information
found in the catalog.

+------------------------+----------------------------+
|   Arguments            |   Description              |
+========================+============================+
| --os-service-type      | service type to request    |
| <name>                 | from the catalog           |
+------------------------+----------------------------+
| --os-service-name      | service name to request    |
| <name>                 | from the catalog           |
+------------------------+----------------------------+
| --os-interface <name>  | API Interface to use:      |
|                        | [public, internal, admin]  |
+------------------------+----------------------------+
| --os-region-name       | region of the cloud to use |
| <name>                 |                            |
+------------------------+----------------------------+
|                        | endpoint to use instead    |
| --os-endpoint-override | of the endpoint in the     |
| <name>                 | catalog                    |
+------------------------+----------------------------+
| --os-api-version       | which version of the       |
| <name>                 | service API to use         |
+------------------------+----------------------------+

_`How to write scenario files`
------------------------------

The example of full scenario file with all these parameters you can find in
``etc/scenario/simple-testcase.yaml``.

You can write all sections in one or several files, which can be simple YAML
files or YAML-based Mako templates (.yaml.mako or yml.mako). Fox example,
the most common sections you can keep in ``templatevars.ini`` and
``sahara_tests/scenario/defaults/credentials.yaml.mako``.

Field "concurrency"
-------------------

This field has integer value, and set concurrency for run tests

For example:
     ``concurrency: 2``

For parallel testing use flag ``--count`` in run command and
setup ``cuncurrency`` value

Section "credentials"
---------------------

This section is dictionary-type.

+---------------------+--------+----------+----------------+----------------+
|   Fields            |  Type  | Required |   Default      |   Value        |
+=====================+========+==========+================+================+
| sahara_service_type | string |          | data-processing| service type   |
|                     |        |          |                | for sahara     |
+---------------------+--------+----------+----------------+----------------+
| sahara_url          | string |          | None           | url of sahara  |
+---------------------+--------+----------+----------------+----------------+
| ssl_cert            | string |          | None           | ssl certificate|
|                     |        |          |                | for all clients|
+---------------------+--------+----------+----------------+----------------+
| ssl_verify          | boolean|          | False          | enable verify  |
|                     |        |          |                | ssl for sahara |
+---------------------+--------+----------+----------------+----------------+

Section "network"
-----------------

This section is dictionary-type.

+-----------------------------+---------+----------+---------+----------------+
|          Fields             |  Type   | Required | Default | Value          |
+=============================+=========+==========+=========+================+
| private_network             | string  |  True    | private | name or id of  |
|                             |         |          |         | private network|
+-----------------------------+---------+----------+---------+----------------+
| public_network              | string  |          | public  | name or id of  |
|                             |         |          |         | private network|
+-----------------------------+---------+----------+---------+----------------+
| type                        | string  |          | neutron | "neutron" or   |
|                             |         |          |         | "nova-network" |
+-----------------------------+---------+----------+---------+----------------+
| auto_assignment_floating_ip | boolean |          | False   |                |
+-----------------------------+---------+----------+---------+----------------+


Section "clusters"
------------------

This sections is an array-type.

.. list-table::
   :header-rows: 1

   * - Fields
     - Type
     - Required
     - Default
     - Value

   * - plugin_name
     - string
     - True
     -
     - name of plugin
   * - plugin_version
     - string
     - True
     -
     - version of plugin
   * - image
     - string
     - True
     -
     - name or id of image
   * - image_username
     - string
     -
     -
     - username for registering image
   * - existing_cluster
     - string
     -
     -
     - cluster name or id for testing
   * - key_name
     - string
     -
     -
     - name of registered ssh key for testing cluster
   * - node_group_templates
     - object
     -
     -
     - see `section "node_group_templates"`_
   * - cluster_template
     - object
     -
     -
     - see `section "cluster_template"`_
   * - cluster
     - object
     -
     -
     - see `section "cluster"`_
   * - scaling
     - object
     -
     -
     - see `section "scaling"`_
   * - timeout_check_transient
     - integer
     -
     - 300
     - timeout for checking transient
   * - timeout_poll_jobs_status
     - integer
     -
     - 1800
     - timeout for polling jobs state
   * - timeout_delete_resource
     - integer
     -
     - 300
     - timeout for delete resource
   * - timeout_poll_cluster_status
     - integer
     -
     - 3600
     - timeout for polling cluster state
   * - scenario
     - array
     -
     - ['run_jobs', 'scale', 'run_jobs']
     - array of checks
   * - edp_jobs_flow
     - string, list
     -
     -
     - name of jobs defined under edp_jobs_flow be executed on the cluster;
       if list, each item may be a dict with fields
       ``name`` (string) and ``features`` (list), or a string
   * - hdfs_username
     - string
     -
     - hadoop
     - username for hdfs
   * - retain_resources
     - boolean
     -
     - False
     -


Section "node_group_templates"
------------------------------

This section is an array-type.


.. list-table::
   :header-rows: 1

   * - Fields
     - Type
     - Required
     - Default
     - Value
   * - name
     - string
     - True
     -
     - name for node group template
   * - flavor
     - string or object
     - True
     -
     - name or id of flavor, or see `section "flavor"`_
   * - node_processes
     - string
     - True
     -
     - name of process
   * - description
     - string
     -
     - Empty
     - description for node group
   * - volumes_per_node
     - integer
     -
     - 0
     - minimum 0
   * - volumes_size
     - integer
     -
     - 0
     - minimum 0
   * - auto_security_group
     - boolean
     -
     - True
     -
   * - security_group
     - array
     -
     -
     - security group
   * - node_configs
     - object
     -
     -
     - name_of_config_section: config: value
   * - availability_zone
     - string
     -
     -
     -
   * - volumes_availability_zone
     - string
     -
     -
     -
   * - volume_type
     - string
     -
     -
     -
   * - is_proxy_gateway
     - boolean
     -
     - False
     - use this node as proxy gateway
   * - edp_batching
     - integer
     -
     - count jobs
     - use for batching jobs


Section "flavor"
----------------

This section is an dictionary-type.

+----------------+---------+----------+---------------+-----------------+
|     Fields     |  Type   | Required |    Default    |      Value      |
+================+=========+==========+===============+=================+
| name           | string  |          | auto-generate | name for flavor |
+----------------+---------+----------+---------------+-----------------+
| id             | string  |          | auto-generate | id for flavor   |
+----------------+---------+----------+---------------+-----------------+
| vcpus          | integer |          |       1       | number of VCPUs |
|                |         |          |               | for the flavor  |
+----------------+---------+----------+---------------+-----------------+
| ram            | integer |          |       1       | memory in MB for|
|                |         |          |               | the flavor      |
+----------------+---------+----------+---------------+-----------------+
| root_disk      | integer |          |       0       | size of local   |
|                |         |          |               | disk in GB      |
+----------------+---------+----------+---------------+-----------------+
| ephemeral_disk | integer |          |       0       | ephemeral space |
|                |         |          |               | in MB           |
+----------------+---------+----------+---------------+-----------------+
| swap_disk      | integer |          |       0       | swap space in MB|
+----------------+---------+----------+---------------+-----------------+


Section "cluster_template"
--------------------------

This section is dictionary-type.

.. list-table::
   :header-rows: 1

   * - Fields
     - Type
     - Required
     - Default
     - Value
   * - name
     - string
     -
     -
     - name for cluster template
   * - description
     - string
     -
     - Empty
     - description
   * - cluster_configs
     - object
     -
     -
     - name_of_config_section: config: value
   * - node_group_templates
     - object
     - True
     -
     - name_of_node_group: count
   * - anti_affinity
     - array
     -
     - Empty
     - array of roles


Section "cluster"
-----------------

This section is dictionary-type.

+--------------+---------+----------+---------+------------------+
|    Fields    |  Type   | Required | Default |       Value      |
+==============+=========+==========+=========+==================+
| name         | string  |          | Empty   | name for cluster |
+--------------+---------+----------+---------+------------------+
| description  | string  |          | Empty   | description      |
+--------------+---------+----------+---------+------------------+
| is_transient | boolean |          | False   | value            |
+--------------+---------+----------+---------+------------------+


Section "scaling"
-----------------

This section is an array-type.

+------------+---------+----------+-----------+--------------------+
|   Fields   |  Type   | Required |  Default  |       Value        |
+============+=========+==========+===========+====================+
| operation  | string  | True     |           | "add" or "resize"  |
+------------+---------+----------+-----------+--------------------+
| node_group | string  | True     | Empty     | name of node group |
+------------+---------+----------+-----------+--------------------+
| size       | integer | True     | Empty     | count node group   |
+------------+---------+----------+-----------+--------------------+


Section "edp_jobs_flow"
-----------------------

This section has an object with a name from the `section "clusters"`_
field "edp_jobs_flows"
Object has sections of array-type.
Required: type

.. list-table::
   :header-rows: 1

   * - Fields
     - Type
     - Required
     - Default
     - Value
   * - type
     - string
     - True
     -
     - "Pig", "Java", "MapReduce", "MapReduce.Streaming", "Hive", "Spark", "Shell"
   * - input_datasource
     - object
     -
     -
     - see `section "input_datasource"`_
   * - output_datasource
     - object
     -
     -
     - see `section "output_datasource"`_
   * - main_lib
     - object
     -
     -
     - see `section "main_lib"`_
   * - additional_libs
     - object
     -
     -
     - see `section "additional_libs"`_
   * - configs
     - dict
     -
     - Empty
     - config: value
   * - args
     - array
     -
     - Empty
     - array of args


Section "input_datasource"
--------------------------

Required: type, source
This section is dictionary-type.

+---------------+--------+----------+-----------+---------------------------+
|    Fields     |  Type  | Required |  Default  |            Value          |
+===============+========+==========+===========+===========================+
| type          | string | True     |           | "swift", "hdfs", "maprfs" |
+---------------+--------+----------+-----------+---------------------------+
| hdfs_username | string |          |           | username for hdfs         |
+---------------+--------+----------+-----------+---------------------------+
| source        | string | True     |           | uri of source             |
+---------------+--------+----------+-----------+---------------------------+


Section "output_datasource"
---------------------------

Required: type, destination
This section is dictionary-type.

+-------------+--------+----------+-----------+---------------------------+
| Fields      |  Type  | Required |  Default  |           Value           |
+=============+========+==========+===========+===========================+
| type        | string | True     |           | "swift", "hdfs", "maprfs" |
+-------------+--------+----------+-----------+---------------------------+
| destination | string | True     |           | uri of source             |
+-------------+--------+----------+-----------+---------------------------+


Section "main_lib"
------------------

Required: type, source
This section is dictionary-type.

+--------+--------+----------+-----------+----------------------+
| Fields |  Type  | Required |  Default  |         Value        |
+========+========+==========+===========+======================+
| type   | string | True     |           | "swift or "database" |
+--------+--------+----------+-----------+----------------------+
| source | string | True     |           | uri of source        |
+--------+--------+----------+-----------+----------------------+


Section "additional_libs"
-------------------------

Required: type, source
This section is an array-type.

+--------+--------+----------+-----------+----------------------+
| Fields |  Type  | Required |  Default  |         Value        |
+========+========+==========+===========+======================+
| type   | string | True     |           | "swift or "database" |
+--------+--------+----------+-----------+----------------------+
| source | string | True     |           | uri of source        |
+--------+--------+----------+-----------+----------------------+
