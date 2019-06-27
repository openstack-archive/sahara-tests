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

from __future__ import print_function
import functools
import logging
import os
import sys
import time
import traceback

import fixtures
from oslo_utils import timeutils
import prettytable
import six
from tempest.lib import base
from tempest.lib.common import ssh as connection
from tempest.lib import exceptions as exc

from sahara_tests.scenario import clients
from sahara_tests.scenario import timeouts
from sahara_tests.scenario import utils
from sahara_tests.utils import crypto as ssh
from sahara_tests.utils import url as utils_url

logger = logging.getLogger('swiftclient')
logger.setLevel(logging.CRITICAL)

CHECK_OK_STATUS = "OK"
CHECK_FAILED_STATUS = "FAILED"
CLUSTER_STATUS_ACTIVE = "Active"
CLUSTER_STATUS_ERROR = "Error"
HEALTH_CHECKS = ["RED", "YELLOW", "GREEN"]


def track_result(check_name, exit_with_error=True):
    def decorator(fct):
        @functools.wraps(fct)
        def wrapper(self, *args, **kwargs):
            started_at = timeutils.utcnow()
            test_info = {
                'check_name': check_name,
                'status': CHECK_OK_STATUS,
                'start_time': started_at,
                'duration': None,
                'traceback': None,
                'exception_time': None
            }
            self._results.append(test_info)
            try:
                return fct(self, *args, **kwargs)
            except Exception:
                test_info['exception_time'] = timeutils.utcnow().strftime(
                    '%Y%m%d_%H%M%S')
                test_info['status'] = CHECK_FAILED_STATUS
                test_info['traceback'] = traceback.format_exception(
                    *sys.exc_info())
                if exit_with_error:
                    raise
            finally:
                test_time = timeutils.utcnow() - started_at
                test_info['duration'] = test_time.seconds
        return wrapper
    return decorator


class BaseTestCase(base.BaseTestCase):

    @classmethod
    def setUpClass(cls):
        super(BaseTestCase, cls).setUpClass()
        cls.network = None
        cls.credentials = None
        cls.testcase = None
        cls._results = []
        cls.report = False
        cls.results_dir = '.'
        cls.default_templ_dir = '.'
        cls.use_api_v2 = False

    def setUp(self):
        super(BaseTestCase, self).setUp()
        self._init_clients()
        timeouts.Defaults.init_defaults(self.testcase)
        self.testcase['ssh_username'] = self.sahara.register_image(
            self.glance.get_image_id(self.testcase['image']),
            self.testcase).username
        self.key = self.testcase.get('key_name')
        if self.key is None:
            self.private_key, self.public_key = ssh.generate_key_pair()
            self.key_name = self.__create_keypair()
        # save the private key if retain_resources is specified
        # (useful for debugging purposes)
        if self.testcase['retain_resources'] or self.key is None:
            private_key_file_name = os.path.join(self.results_dir,
                                                 self.key_name + '.key')
            with open(private_key_file_name, 'w+') as private_key_file:
                private_key_file.write(self.private_key)
            os.chmod(private_key_file_name, 0o600)
        self.plugin_version_option = 'plugin_version'
        if not self.use_api_v2:
            self.plugin_version_option = 'hadoop_version'
        self.plugin_opts = {
            'plugin_name': self.testcase['plugin_name'],
            self.plugin_version_option: self.testcase['plugin_version']
        }
        self.cinder = True
        self.proxy = False

    def _init_clients(self):
        username = self.credentials['os_username']
        password = self.credentials['os_password']
        tenant_name = self.credentials['os_tenant']
        auth_url = self.credentials['os_auth_url']
        sahara_service_type = self.credentials['sahara_service_type']
        sahara_url = self.credentials['sahara_url']
        auth_version = '3.0' if 'v3' in auth_url else '2.0'
        session = clients.get_session(auth_url, username, password,
                                      tenant_name,
                                      self.credentials.get('ssl_verify',
                                                           False),
                                      self._get_file_with_defaults(
                                          self.credentials.get('ssl_cert')))

        api_version = '2' if self.use_api_v2 else '1.1'
        self.sahara = clients.SaharaClient(session=session,
                                           service_type=sahara_service_type,
                                           sahara_url=sahara_url,
                                           api_version=api_version)
        self.nova = clients.NovaClient(session=session)
        self.neutron = clients.NeutronClient(session=session)
        # swiftclient doesn't support keystone sessions
        self.swift = clients.SwiftClient(
            auth_version=auth_version,
            authurl=auth_url,
            user=username,
            key=password,
            insecure=not self.credentials.get('ssl_verify', False),
            cacert=self.credentials.get('ssl_cert'),
            tenant_name=tenant_name)
        self.glance = clients.GlanceClient(session=session)
        # boto is not an OpenStack client, but we can handle it as well
        self.boto = None
        if self.credentials.get("s3_endpoint", None):
            self.boto = clients.BotoClient(
                endpoint=self.credentials["s3_endpoint"],
                accesskey=self.credentials["s3_accesskey"],
                secretkey=self.credentials["s3_secretkey"])

    def create_cluster(self):
        self.cluster_id = self.sahara.get_cluster_id(
            self.testcase.get('existing_cluster'))
        self.ng_id_map = {}
        if self.cluster_id is None:
            self.ng_id_map = self._create_node_group_templates()
            cl_tmpl_id = self._create_cluster_template()
            self.cluster_id = self._create_cluster(cl_tmpl_id)
        elif self.key is None:
            self.cinder = False
        self._poll_cluster_status_tracked(self.cluster_id)
        cluster = self.sahara.get_cluster(self.cluster_id, show_progress=True)
        self._get_proxy(cluster)
        self.check_cinder()
        if self.check_feature_available("provision_progress"):
            self._check_event_logs(cluster)

    def _get_proxy(self, cluster):
        for ng in cluster.node_groups:
            if ng['is_proxy_gateway']:
                for instance in ng['instances']:
                    if instance['management_ip'] != (
                            instance['internal_ip']):
                        self.proxy = instance['management_ip']

    @track_result("Check transient")
    def check_transient(self):
        with fixtures.Timeout(
                timeouts.Defaults.instance.timeout_check_transient,
                gentle=True):
            while True:
                if self.sahara.is_resource_deleted(
                        self.sahara.get_cluster_status, self.cluster_id):
                    break
                time.sleep(5)

    def _inject_datasources_data(self, arg, input_url, output_url):
        return arg.format(
            input_datasource=input_url, output_datasource=output_url)

    def _put_io_data_to_configs(self, configs, input_id, output_id):
        input_url, output_url = None, None
        if input_id is not None:
            input_url = self.sahara.get_datasource(
                data_source_id=input_id).url
        if output_id is not None:
            output_url = self.sahara.get_datasource(
                data_source_id=output_id).url
        pl = lambda x: self._inject_datasources_data(x, input_url, output_url)
        args = list(map(pl, configs.get('args', [])))
        configs['args'] = args
        return configs

    def _prepare_job_running(self, job):
        input_id, output_id = self._create_datasources(job)
        main_libs, additional_libs = self._create_job_binaries(job)
        job_id = self._create_job(job['type'], main_libs, additional_libs)
        configs = self._parse_job_configs(job)
        configs = self._put_io_data_to_configs(
            configs, input_id, output_id)
        return [job_id, input_id, output_id, configs]

    @track_result("Check EDP jobs", False)
    def check_run_jobs(self):
        batching = self.testcase.get('edp_batching',
                                     len(self.testcase['edp_jobs_flow']))
        batching_size = batching
        jobs = self.testcase.get('edp_jobs_flow', [])

        pre_exec = []
        for job in jobs:
            pre_exec.append(self._prepare_job_running(job))
            batching -= 1
            if not batching:
                self._job_batching(pre_exec)
                pre_exec = []
                batching = batching_size
        self.check_verification(self.cluster_id)

    def _job_batching(self, pre_exec):
        job_exec_ids = []
        for job_exec in pre_exec:
            job_exec_ids.append(self._run_job(*job_exec))

        self._poll_jobs_status(job_exec_ids)

    def _create_datasources(self, job):
        def create(ds, name):
            credential_vars = {}
            source = ds.get('source', None)
            destination = None if source else utils.rand_name(
                ds['destination'])
            if ds['type'] == 'swift':
                url = self._create_swift_data(source, destination)
                credential_vars = {
                    'credential_user': self.credentials['os_username'],
                    'credential_pass': self.credentials['os_password']
                }
            elif ds['type'] == 's3':
                url = self._create_s3_data(source, destination)
                credential_vars = {
                    's3_credentials': {
                        'accesskey': self.credentials['s3_accesskey'],
                        'secretkey': self.credentials['s3_secretkey'],
                        'endpoint': utils_url.url_schema_remover(
                            self.credentials['s3_endpoint']),
                        'ssl': self.credentials['s3_endpoint_ssl'],
                        'bucket_in_path': self.credentials['s3_bucket_path']
                    }
                }
            elif ds['type'] == 'hdfs':
                url = self._create_dfs_data(source, destination,
                                            self.testcase.get('hdfs_username',
                                                              'hadoop'),
                                            ds['type'])
            elif ds['type'] == 'maprfs':
                url = self._create_dfs_data(source, destination,
                                            ds.get('maprfs_username', 'mapr'),
                                            ds['type'])
            return self.__create_datasource(
                name=utils.rand_name(name),
                description='',
                data_source_type=ds['type'], url=url,
                **credential_vars)

        input_id, output_id = None, None
        if job.get('input_datasource'):
            ds = job['input_datasource']
            input_id = create(ds, 'input')

        if job.get('output_datasource'):
            ds = job['output_datasource']
            output_id = create(ds, 'output')

        return input_id, output_id

    def _create_job_binaries(self, job):
        main_libs = []
        additional_libs = []
        if job.get('main_lib'):
            main_libs.append(self._create_job_binary(job['main_lib']))
        for add_lib in job.get('additional_libs', []):
            lib_id = self._create_job_binary(add_lib)
            additional_libs.append(lib_id)

        return main_libs, additional_libs

    def _create_job_binary(self, job_binary):
        url = None
        extra = {}
        if job_binary['type'] == 'swift':
            url = self._create_swift_data(job_binary['source'])
            extra['user'] = self.credentials['os_username']
            extra['password'] = self.credentials['os_password']
        elif job_binary['type'] == 's3':
            url = self._create_s3_data(job_binary['source'])
            extra['accesskey'] = self.credentials['s3_accesskey']
            extra['secretkey'] = self.credentials['s3_secretkey']
            extra['endpoint'] = self.credentials['s3_endpoint']
        elif job_binary['type'] == 'database':
            url = self._create_internal_db_data(job_binary['source'])

        job_binary_name = '%s-%s' % (
            utils.rand_name('test'), os.path.basename(job_binary['source']))
        return self.__create_job_binary(job_binary_name, url, '', extra)

    def _create_job(self, type, mains, libs):
        return self.__create_job(utils.rand_name('test'), type, mains,
                                 libs, '')

    def _parse_job_configs(self, job):
        configs = {}
        if job.get('configs'):
            configs['configs'] = {}
            for param, value in six.iteritems(job['configs']):
                configs['configs'][param] = str(value)
        if job.get('args'):
            configs['args'] = list(map(str, job['args']))
        return configs

    def _run_job(self, job_id, input_id, output_id, configs):
        return self.__run_job(job_id, self.cluster_id, input_id, output_id,
                              configs)

    def _poll_jobs_status(self, exec_ids):
        try:
            with fixtures.Timeout(
                    timeouts.Defaults.instance.timeout_poll_jobs_status,
                    gentle=True):
                success = False
                polling_ids = list(exec_ids)
                while not success:
                    current_ids = list(polling_ids)
                    success = True
                    for exec_id in polling_ids:
                        status = self.sahara.get_job_status(exec_id)
                        if status not in ['FAILED', 'KILLED', 'DONEWITHERROR',
                                          "SUCCEEDED"]:
                            success = False
                        else:
                            current_ids.remove(exec_id)
                    polling_ids = list(current_ids)
                    time.sleep(5)
        finally:
            report = []
            for exec_id in exec_ids:
                status = self.sahara.get_job_status(exec_id)
                if status != "SUCCEEDED":
                    info = self.sahara.get_job_info(exec_id)
                    report.append("Job with id={id}, name={name}, "
                                  "type={type} has status "
                                  "{status}".format(id=exec_id,
                                                    name=info.name,
                                                    type=info.type,
                                                    status=status))
            if report:
                self.fail("\n".join(report))

    def _get_file_with_defaults(self, file_path):
        """ Check if the file exists; if it is a relative path, check also
            among the default files.
        """
        if not file_path:
            return ''

        all_files = [file_path]
        if not os.path.isabs(file_path):
            # relative path: look into default templates too, if defined
            default_file = os.path.join(self.default_templ_dir, file_path)
            if os.path.abspath(default_file) != os.path.abspath(file_path):
                all_files.append(default_file)
        for checked_file in all_files:
            if os.path.isfile(checked_file):
                return checked_file
        raise Exception('File %s not found while looking into %s' %
                        (file_path, all_files))

    def _read_source_file(self, source):
        if not source:
            return None
        with open(self._get_file_with_defaults(source), 'rb') as source_fd:
            data = source_fd.read()
        return data

    def _create_swift_data(self, source=None, destination=None):
        container = self._get_swift_container()
        path = utils.rand_name(destination if destination else 'test')
        data = self._read_source_file(source)

        self.__upload_to_container(container, path, data)

        return 'swift://%s.sahara/%s' % (container, path)

    def _create_s3_data(self, source=None, destination=None):
        bucket = self._get_s3_bucket()
        path = utils.rand_name(destination if destination else 'test')
        data = self._read_source_file(source)

        self.__upload_to_bucket(bucket, path, data)

        return 's3://%s/%s' % (bucket, path)

    def _create_dfs_data(self, source, destination, hdfs_username, fs):

        def to_hex_present(string):
            return "".join(map(lambda x: hex(ord(x)).replace("0x", "\\x"),
                               string.decode('utf-8')))
        if destination:
            return destination

        command_prefixes = {'hdfs': 'hdfs dfs',
                            'maprfs': 'hadoop fs'}

        hdfs_dir = utils.rand_name("/user/%s/data" % hdfs_username)
        instances = self._get_nodes_with_process('namenode')
        if len(instances) == 0:
            instances = self._get_nodes_with_process('CLDB')
        inst_ip = instances[0]["management_ip"]
        self._run_command_on_node(
            inst_ip,
            "sudo su - -c \"%(prefix)s -mkdir -p %(path)s \" %(user)s" % {
                "prefix": command_prefixes[fs],
                "path": hdfs_dir,
                "user": hdfs_username})
        hdfs_filepath = utils.rand_name(hdfs_dir + "/file")
        data = self._read_source_file(source)
        if not data:
            data = ''
        self._run_command_on_node(
            inst_ip,
            ("echo -e \"%(data)s\" | sudo su - -c \"%(prefix)s"
             " -put - %(path)s\" %(user)s") % {
                "data": to_hex_present(data),
                "prefix": command_prefixes[fs],
                "path": hdfs_filepath,
                "user": hdfs_username})
        return hdfs_filepath

    def _create_internal_db_data(self, source):
        data = self._read_source_file(source)
        id = self.__create_internal_db_data(utils.rand_name('test'), data)
        return 'internal-db://%s' % id

    def _get_swift_container(self):
        if not getattr(self, '__swift_container', None):
            self.__swift_container = self.__create_container(
                utils.rand_name('sahara-tests'))
        return self.__swift_container

    def _get_s3_bucket(self):
        if not getattr(self, '__s3_bucket', None):
            self.__s3_bucket = self.__create_bucket(
                utils.rand_name('sahara-tests'))
        return self.__s3_bucket

    @track_result("Cluster scaling", False)
    def check_scale(self):
        scale_ops = []
        ng_before_scale = self.sahara.get_cluster(self.cluster_id).node_groups
        scale_ops = self.testcase['scaling']

        body = {}
        for op in scale_ops:
            node_scale = op['node_group']
            if op['operation'] == 'add':
                if 'add_node_groups' not in body:
                    body['add_node_groups'] = []
                body['add_node_groups'].append({
                    'node_group_template_id':
                    self.ng_id_map.get(node_scale,
                                       self.sahara.get_node_group_template_id(
                                           node_scale)),
                    'count': op['size'],
                    'name': utils.rand_name(node_scale)
                })
            if op['operation'] == 'resize':
                if 'resize_node_groups' not in body:
                    body['resize_node_groups'] = []
                body['resize_node_groups'].append({
                    'name': self.ng_name_map.get(
                        node_scale,
                        self.sahara.get_node_group_template_id(node_scale)),
                    'count': op['size']
                })

        if body:
            self.sahara.scale_cluster(self.cluster_id, body)
            self._poll_cluster_status(self.cluster_id)
            ng_after_scale = self.sahara.get_cluster(
                self.cluster_id).node_groups
            self._validate_scaling(ng_after_scale,
                                   self._get_expected_count_of_nodes(
                                       ng_before_scale, body))

    def _validate_scaling(self, after, expected_count):
        for (key, value) in six.iteritems(expected_count):
            ng = {}
            for after_ng in after:
                if after_ng['name'] == key:
                    ng = after_ng
                    break
            self.assertEqual(value, ng.get('count', 0))

    def _get_expected_count_of_nodes(self, before, body):
        expected_mapper = {}
        for ng in before:
            expected_mapper[ng['name']] = ng['count']
        for ng in body.get('add_node_groups', []):
            expected_mapper[ng['name']] = ng['count']
        for ng in body.get('resize_node_groups', []):
            expected_mapper[ng['name']] = ng['count']
        return expected_mapper

    @track_result("Check cinder volumes")
    def check_cinder(self):
        if not self._get_node_list_with_volumes() or not self.cinder:
            print("All tests for Cinder were skipped")
            return
        for node_with_volumes in self._get_node_list_with_volumes():
            volume_count_on_node = int(self._run_command_on_node(
                node_with_volumes['node_ip'],
                'mount | grep %s | wc -l' %
                node_with_volumes['volume_mount_prefix']
            ))
            self.assertEqual(
                node_with_volumes['volume_count'], volume_count_on_node,
                'Some volumes were not mounted to node.\n'
                'Expected count of mounted volumes to node is %s.\n'
                'Actual count of mounted volumes to node is %s.'
                % (node_with_volumes['volume_count'], volume_count_on_node)
            )

    def _get_node_list_with_volumes(self):
        node_groups = self.sahara.get_cluster(self.cluster_id).node_groups
        node_list_with_volumes = []
        for node_group in node_groups:
            if node_group['volumes_per_node'] != 0:
                for instance in node_group['instances']:
                    node_list_with_volumes.append({
                        'node_ip': instance['management_ip'],
                        'volume_count': node_group['volumes_per_node'],
                        'volume_mount_prefix':
                            node_group['volume_mount_prefix']
                    })
        return node_list_with_volumes

    @track_result("Create node group templates")
    def _create_node_group_templates(self):
        ng_id_map = {}
        floating_ip_pool = None
        security_group = None
        proxy_exist = False

        if self.network['public_network']:
            if self.network['type'] == 'neutron':
                floating_ip_pool = self.neutron.get_network_id(
                    self.network['public_network'])
            elif not self.network['auto_assignment_floating_ip']:
                floating_ip_pool = self.network['public_network']

        node_groups = []
        for ng in self.testcase['node_group_templates']:
            node_groups.append(ng)
            if ng.get('is_proxy_gateway', False):
                proxy_exist = True

        for ng in node_groups:
            kwargs = dict(ng)
            kwargs.update(self.plugin_opts)
            kwargs['flavor_id'] = self._get_flavor_id(kwargs['flavor'])
            del kwargs['flavor']
            kwargs['name'] = utils.rand_name(kwargs['name'])
            if (not proxy_exist) or (proxy_exist and kwargs.get(
                    'is_proxy_gateway', False)):
                kwargs['floating_ip_pool'] = floating_ip_pool
            if not kwargs.get('auto_security_group', True):
                if security_group is None:
                    sg_name = utils.rand_name('scenario')
                    security_group = self.__create_security_group(sg_name)
                    self.neutron.add_security_group_rule_for_neutron(
                        security_group)
                kwargs['security_groups'] = [security_group]

            # boot_from_volume requires APIv2
            if kwargs.get('boot_from_volume', False) and not self.use_api_v2:
                raise Exception('boot_from_volume is set for %s but it '
                                'requires APIv2' % (kwargs['name']))

            ng_id = self.__create_node_group_template(**kwargs)
            ng_id_map[ng['name']] = ng_id
        return ng_id_map

    @track_result("Set flavor")
    def _get_flavor_id(self, flavor):
        if isinstance(flavor, six.string_types):
            return self.nova.get_flavor_id(flavor)
        else:
            # if the name already exists, use it
            if flavor.get('name'):
                try:
                    return self.nova.get_flavor_id(flavor['name'])
                except exc.NotFound:
                    print("Custom flavor %s not found, it will be created" %
                          (flavor['name']))

            flavor_id = self.nova.create_flavor(flavor).id
            self.addCleanup(self.nova.delete_flavor, flavor_id)
            return flavor_id

    @track_result("Create cluster template")
    def _create_cluster_template(self):
        self.ng_name_map = {}
        template = self.testcase['cluster_template']

        kwargs = dict(template)
        ngs = kwargs['node_group_templates']
        del kwargs['node_group_templates']
        kwargs['node_groups'] = []
        for ng, count in ngs.items():
            ng_name = utils.rand_name(ng)
            self.ng_name_map[ng] = ng_name
            kwargs['node_groups'].append({
                'name': ng_name,
                'node_group_template_id': self.ng_id_map[ng],
                'count': count})

        kwargs.update(self.plugin_opts)
        kwargs['name'] = utils.rand_name(kwargs.get('name', 'ct'))
        if self.network['type'] == 'neutron':
            kwargs['net_id'] = self.neutron.get_network_id(
                self.network['private_network'])

        return self.__create_cluster_template(**kwargs)

    @track_result("Check event logs")
    def _check_event_logs(self, cluster):
        invalid_steps = []
        if cluster.is_transient:
            # skip event log testing
            return

        for step in cluster.provision_progress:
            if not step['successful']:
                invalid_steps.append(step)

        if len(invalid_steps) > 0:
            invalid_steps_info = "\n".join(six.text_type(e)
                                           for e in invalid_steps)
            steps_info = "\n".join(six.text_type(e)
                                   for e in cluster.provision_progress)
            raise exc.TempestException(
                "Issues with event log work: "
                "\n Incomplete steps: \n\n {invalid_steps}"
                "\n All steps: \n\n {steps}".format(
                    steps=steps_info,
                    invalid_steps=invalid_steps_info))

    @track_result("Create cluster")
    def _create_cluster(self, cluster_template_id):
        if self.testcase.get('cluster'):
            kwargs = dict(self.testcase['cluster'])
        else:
            kwargs = {}  # default template

        kwargs.update(self.plugin_opts)
        kwargs['name'] = utils.rand_name(kwargs.get('name', 'test'))
        kwargs['cluster_template_id'] = cluster_template_id
        kwargs['default_image_id'] = self.glance.get_image_id(
            self.testcase['image'])
        kwargs['user_keypair_id'] = self.key_name

        return self.__create_cluster(**kwargs)

    @track_result("Check cluster state")
    def _poll_cluster_status_tracked(self, cluster_id):
        self._poll_cluster_status(cluster_id)

    def _poll_cluster_status(self, cluster_id):
        with fixtures.Timeout(
                timeouts.Defaults.instance.timeout_poll_cluster_status,
                gentle=True):
            while True:
                status = self.sahara.get_cluster_status(cluster_id)
                if status == CLUSTER_STATUS_ACTIVE:
                    break
                if status == CLUSTER_STATUS_ERROR:
                    cluster = self.sahara.get_cluster(cluster_id)
                    failure_desc = cluster.status_description
                    message = ("Cluster in %s state with"
                               " a message below:\n%s") % (status,
                                                           failure_desc)

                    raise exc.TempestException(message)
                time.sleep(3)

    def _run_command_on_node(self, node_ip, command):
        host_ip = node_ip
        if self.proxy:
            host_ip = self.proxy
            command = ("echo '{pkey}' > {filename} && chmod 600 {filename} && "
                       "ssh -o StrictHostKeyChecking=no {ip} -i {filename} "
                       "'{cmd}' && rm {filename}".format(
                           pkey=self.private_key, filename='scenario.pem',
                           ip=node_ip, cmd=command))
        ssh_session = connection.Client(host_ip, self.testcase['ssh_username'],
                                        pkey=self.private_key)
        return ssh_session.exec_command(command)

    def _get_nodes_with_process(self, process=None):
        if process is not None:
            process = process.lower()
        nodegroups = self.sahara.get_cluster(self.cluster_id).node_groups
        nodes_with_process = []
        for nodegroup in nodegroups:
            for node_process in nodegroup['node_processes']:
                if not process or process in node_process.lower():
                    nodes_with_process.extend(nodegroup['instances'])
        return nodes_with_process

    def _get_health_status(self, cluster):
        try:
            return cluster.verification['status']
        except (AttributeError, KeyError):
            return 'UNKNOWN'

    def _poll_verification_status(self, cluster_id):
        with fixtures.Timeout(
                timeouts.Defaults.instance.timeout_poll_cluster_status,
                gentle=True):
            while True:
                cluster = self.sahara.get_cluster(cluster_id)
                status = self._get_health_status(cluster)
                if status == 'UNKNOWN':
                    print("Cluster verification did not start")
                    break
                if status in HEALTH_CHECKS:
                    break
                time.sleep(3)

    @track_result("Check cluster verification")
    def check_verification(self, cluster_id):
        if self.check_feature_available("verification"):
            self._poll_cluster_status(cluster_id)

            # need to check if previous verification check is not
            # in the status CHECKING
            self._poll_verification_status(cluster_id)
            self.sahara.start_cluster_verification(cluster_id)

            # check if this verification check finished without errors
            self._poll_verification_status(cluster_id)
        else:
            print("All tests for cluster verification were skipped")

    # client ops

    def __create_node_group_template(self, *args, **kwargs):
        id = self.sahara.create_node_group_template(*args, **kwargs)
        if not self.testcase['retain_resources']:
            self.addCleanup(self.sahara.delete_node_group_template, id)
        return id

    def __create_security_group(self, sg_name):
        id = self.neutron.create_security_group_for_neutron(sg_name)
        if not self.testcase['retain_resources']:
            self.addCleanup(self.neutron.delete_security_group_for_neutron, id)
        return id

    def __create_cluster_template(self, *args, **kwargs):
        id = self.sahara.create_cluster_template(*args, **kwargs)
        if not self.testcase['retain_resources']:
            self.addCleanup(self.sahara.delete_cluster_template, id)
        return id

    def __create_cluster(self, *args, **kwargs):
        id = self.sahara.create_cluster(*args, **kwargs)
        if not self.testcase['retain_resources']:
            self.addCleanup(self.sahara.delete_cluster, id)
        return id

    def __create_datasource(self, *args, **kwargs):
        id = self.sahara.create_datasource(*args, **kwargs)
        if not self.testcase['retain_resources']:
            self.addCleanup(self.sahara.delete_datasource, id)
        return id

    def __create_internal_db_data(self, *args, **kwargs):
        id = self.sahara.create_job_binary_internal(*args, **kwargs)
        if not self.testcase['retain_resources']:
            self.addCleanup(self.sahara.delete_job_binary_internal, id)
        return id

    def __create_job_binary(self, *args, **kwargs):
        id = self.sahara.create_job_binary(*args, **kwargs)
        if not self.testcase['retain_resources']:
            self.addCleanup(self.sahara.delete_job_binary, id)
        return id

    def __create_job(self, *args, **kwargs):
        id = self.sahara.create_job_template(*args, **kwargs)
        if not self.testcase['retain_resources']:
            self.addCleanup(self.sahara.delete_job_template, id)
        return id

    def __run_job(self, *args, **kwargs):
        id = self.sahara.run_job(*args, **kwargs)
        if not self.testcase['retain_resources']:
            self.addCleanup(self.sahara.delete_job_execution, id)
        return id

    def __create_container(self, container_name):
        self.swift.create_container(container_name)
        if not self.testcase['retain_resources']:
            self.addCleanup(self.swift.delete_container, container_name)
        return container_name

    def __upload_to_container(self, container_name, object_name, data=None):
        if data:
            self.swift.upload_data(container_name, object_name, data)
        if not self.testcase['retain_resources']:
            self.addCleanup(self.swift.delete_object, container_name,
                            object_name)

    def __create_bucket(self, bucket_name):
        self.boto.create_bucket(bucket_name)
        if not self.testcase['retain_resources']:
            self.addCleanup(self.boto.delete_bucket, bucket_name)
        return bucket_name

    def __upload_to_bucket(self, bucket_name, object_name, data=None):
        if data:
            self.boto.upload_data(bucket_name, object_name, data)
        if not self.testcase['retain_resources']:
            self.addCleanup(self.boto.delete_object, bucket_name,
                            object_name)

    def __create_keypair(self):
        key = utils.rand_name('scenario_key')
        self.nova.nova_client.keypairs.create(key,
                                              public_key=self.public_key)
        if not self.testcase['retain_resources']:
            self.addCleanup(self.nova.delete_keypair, key)
        return key

    def check_feature_available(self, feature_name):
        if not getattr(self.sahara.get_cluster(self.cluster_id),
                       feature_name, None):
            return False
        return True

    def tearDown(self):
        tbs = []
        table = prettytable.PrettyTable(["Check", "Status", "Duration, s",
                                         "Start time"])
        table.align["Check"] = "l"
        for check in self._results:
            table.add_row(
                [check['check_name'], check['status'], check['duration'],
                 check['start_time']])
            if check['status'] == CHECK_FAILED_STATUS:
                tbs.append(check['exception_time'])
                tbs.extend(check['traceback'])
                tbs.append("")
        print("Results of testing plugin", self.plugin_opts['plugin_name'],
              self.plugin_opts[self.plugin_version_option])
        print(table)
        print("\n".join(tbs), file=sys.stderr)

        super(BaseTestCase, self).tearDown()

        test_failed = any([c['status'] == CHECK_FAILED_STATUS
                           for c in self._results])

        if self.report:
            filename = {"time": time.strftime('%Y%m%d%H%M%S',
                                              time.localtime())}
            filename.update(self.plugin_opts)
            # let's normalize this variable so that we can use
            # a stable name as formatter later.
            if 'hadoop_version' in filename:
                filename['plugin_version'] = filename['hadoop_version']
                del filename['hadoop_version']
            report_file_name = os.path.join(
                self.results_dir,
                '{plugin_name}_{plugin_version}-{time}'.format(**filename))
            time.strftime('%Y%m%d%H%M%S', time.localtime())
            with open(report_file_name, 'w+') as report_file:
                report_file.write(str(self._results))
            print("Results can be found in %s" % report_file_name)
        if test_failed:
            self.fail("Scenario tests failed")
