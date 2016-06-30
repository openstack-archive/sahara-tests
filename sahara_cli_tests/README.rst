================
Sahara CLI Tests
================

This directory contains tests to cover CLI commands of saharaclient.

To run these tests, you need export the next variables:
    - OS_USERNAME
    - OS_TENANT_NAME
    - OS_PASSWORD
    - OS_AUTH_URL

Also you need to install saharaclient on env, and Sahara should be correctly
configured and be working.

After this, you just run tests with the command:

.. sourcecode:: console

    $ tox -e cli-tests
..
