=========
Sahara CI
=========

The files in this directory are needed for the sahara continuous
integration tests. Modifying these files will change the behavior of the
tests.

Details
-------

Key values (mako variables):

* ${network_private_name}, ${network_public_name} - names of private (tenant) and public networks;
* ${cluster_name} - name of cluster, which generating from $HOST-$ZUUL_CHANGE-$CLUSTER_HASH. Where:
    * $HOST - host id;
    * $ZUUL_CHANGE - change number;
    * $CLUSTER_HASH - hash, which generating for each cluster by using "uuid" python module;
* ${<plugin>_image} - name of image for each plugin;
* flavor ids:
    * ${ci_flavor} - 2GB RAM, 1 VCPU, 40GB Root disk;
    * ${medium_flavor} - 4GB RAM, 2 VCPUs, 40GB Root disk;
    * ${large_flavor} - 8GB RAM, 4 VCPUs, 80GB Root disk;

Main URLs
---------

https://sahara.mirantis.com/jenkins - Sahara CI Jenkins
https://github.com/openstack/sahara-ci-config/ - Sahara CI Config repo
