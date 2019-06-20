Tempest Integration of Sahara
=============================

Sahara Tempest plugin contains api, cli and clients tests.

There are several ways to run Tempest tests: it is possible to run them using
your Devstack or using Rally.

Run Tempest tests on Devstack
-----------------------------

See how to configure Tempest at
`Tempest Configuration Guide <https://docs.openstack.org/tempest/latest/configuration.html>`_.

Tempest automatically discovers installed plugins. That's why you just need to
install the Python packages that contains the Sahara Tempest plugin in the
same environment where Tempest is installed.

.. sourcecode:: console

    $ git clone https://opendev.org/openstack/sahara-tests
    $ cd sahara-tests/
    $ pip install sahara-tests/

..

After that you can run Tempest tests. You can specify the name of
test or a more complex regular expression. While any ``testr``-based
test runner can be used, the official command for executing Tempest
tests is ``tempest run``.

For example, the following command will run a specific subset of tests:

.. sourcecode:: console

    $ tempest run --regex '^sahara_tempest_plugin.tests.cli.test_scenario.Scenario.'

..

The full syntax of ``tempest run`` is described on `the relavant section of
the Tempest documentation <https://docs.openstack.org/tempest/latest/run.html>`_.

Other useful links:

* `Using Tempest plugins <https://docs.openstack.org/tempest/latest/plugin.html#using-plugins>`_.
* `Tempest Quickstart <https://docs.openstack.org/tempest/latest/overview.html#quickstart>`_.

Run Tempest tests using Rally
-----------------------------

First of all, be sure that Rally is installed and working. There should be
a Rally deployment with correct working Sahara service in it.

Full information can be found on the
`rally quick start guide <https://docs.openstack.org/rally/latest/quick_start/tutorial/step_9_verifying_cloud_via_tempest_verifier.html>`_.

Using this information, you can install ``rally verify`` tool and plugin for
testing Sahara. After this you are free to run Sahara Tempest tests. Here are
some examples of how to run all the tests:

.. sourcecode:: console

    $ rally verify start --pattern sahara_tempest_plugin.tests

..

If you want to run client or cli tests, you need to add the following line to
generated config in ``[data-processing]`` field:

.. sourcecode:: bash

    test_image_name = IMAGE_NAME

..

where ``IMAGE_NAME`` is the name of image on which you would like to run tests.
