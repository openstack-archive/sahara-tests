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

import mock
from saharaclient.api import cluster_templates
from saharaclient.api import clusters
from saharaclient.api import data_sources
from saharaclient.api import images
from saharaclient.api import job_binaries
from saharaclient.api import job_binary_internals
from saharaclient.api import job_executions
from saharaclient.api import jobs
from saharaclient.api import node_group_templates
from saharaclient.api import plugins
from tempest.lib import exceptions as exc
import testtools

from sahara_tests.scenario import base
from sahara_tests.scenario import timeouts


class FakeSaharaClient(object):
    def __init__(self):
        self.clusters = clusters.ClusterManager(None)
        self.cluster_templates = cluster_templates.ClusterTemplateManager(None)
        self.node_group_templates = (node_group_templates.
                                     NodeGroupTemplateManager(None))
        self.plugins = plugins.PluginManager(None)
        self.images = images.ImageManager(None)
        self.data_sources = data_sources.DataSourceManager(None)
        self.jobs = jobs.JobsManager(None)
        self.job_executions = job_executions.JobExecutionsManager(None)
        self.job_binaries = job_binaries.JobBinariesManager(None)
        self.job_binary_internals = (
            job_binary_internals.JobBinaryInternalsManager(None))


class FakeCluster(object):
    def __init__(self, is_transient=False, provision_progress=[], ng=[]):
        self.is_transient = is_transient
        self.provision_progress = provision_progress
        self.node_groups = ng


class FakeResponse(object):
    def __init__(self, set_id=None, set_status=None, status_description=None,
                 node_groups=None, url=None, job_id=None, name=None,
                 job_type=None, verification=None):
        self.id = set_id
        self.status = set_status
        self.status_description = status_description
        self.node_groups = node_groups
        self.url = url
        self.job_id = job_id
        self.name = name
        self.type = job_type
        self.verification = verification


class FakeFlavor(object):
    def __init__(self, flavor_id=None, name=None):
        self.id = flavor_id
        self.name = name


class TestBase(testtools.TestCase):
    def setUp(self):
        super(TestBase, self).setUp()
        with mock.patch(
                'sahara_tests.scenario.base.BaseTestCase.__init__'
        ) as mock_init:
            mock_init.return_value = None
            self.base_scenario = base.BaseTestCase()
        self.base_scenario.credentials = {'os_username': 'admin',
                                          'os_password': 'nova',
                                          'os_tenant': 'admin',
                                          'os_auth_url':
                                              'http://localhost:5000/v2.0',
                                          's3_accesskey': 'very_long_key',
                                          's3_secretkey': 'very_long_secret',
                                          's3_endpoint': 'https://localhost',
                                          'sahara_service_type':
                                              'data-processing-local',
                                          'sahara_url':
                                              'http://sahara_host:8386/v1.1',
                                          'ssl_cert': 'sahara_tests/unit/'
                                                      'scenario/dummy.crt',
                                          'ssl_verify': True}
        self.base_scenario.plugin_opts = {'plugin_name': 'vanilla',
                                          'hadoop_version': '2.7.1'}
        self.base_scenario.network = {'type': 'neutron',
                                      'private_network': 'changed_private',
                                      'public_network': 'changed_public',
                                      'auto_assignment_floating_ip': False}
        self.base_scenario.testcase = {
            'node_group_templates': [
                {
                    'name': 'master',
                    'node_processes': ['namenode', 'oozie', 'resourcemanager'],
                    'flavor': '2',
                    'is_proxy_gateway': True
                },
                {
                    'name': 'worker',
                    'node_processes': ['datanode', 'nodemanager'],
                    'flavor': '2'
                }],
            'cluster_template': {
                'name': 'test_name_ct',
                'node_group_templates': {
                    'master': 1,
                    'worker': 3
                }
            },
            'timeout_poll_cluster_status': 300,
            'timeout_delete_resource': 300,
            'timeout_poll_jobs_status': 2,
            'timeout_check_transient': 3,
            'retain_resources': True,
            'image': 'image_name',
            'edp_batching': 1,
            "edp_jobs_flow": {
                "test_flow": [
                    {
                        "type": "Pig",
                        "input_datasource": {
                            "type": "swift",
                            "source": "sahara_tests/scenario/defaults/"
                                      "edp-examples/edp-pig/"
                                      "top-todoers/data/input"
                        },
                        "output_datasource": {
                            "type": "hdfs",
                            "destination": "/user/hadoop/edp-output"
                        },
                        "main_lib": {
                            "type": "s3",
                            "source": "sahara_tests/scenario/defaults/"
                                      "edp-examples/edp-pig/"
                                      "top-todoers/example.pig"
                        }
                    }
                ]
            }
        }
        self.base_scenario.ng_id_map = {'worker': 'set_id', 'master': 'set_id'}
        self.base_scenario.ng_name_map = {}
        self.base_scenario.key_name = 'test_key'
        self.base_scenario.key = 'key_from_yaml'
        self.base_scenario.template_path = ('sahara_tests/scenario/templates/'
                                            'vanilla/2.7.1')
        self.job = self.base_scenario.testcase["edp_jobs_flow"].get(
            'test_flow')[0]
        self.base_scenario.cluster_id = 'some_id'
        self.base_scenario.proxy_ng_name = False
        self.base_scenario.proxy = False
        self.base_scenario.setUpClass()
        timeouts.Defaults.init_defaults(self.base_scenario.testcase)

    @mock.patch('keystoneauth1.identity.v3.Password')
    @mock.patch('keystoneauth1.session.Session')
    @mock.patch('glanceclient.client.Client', return_value=None)
    @mock.patch('saharaclient.client.Client', return_value=None)
    @mock.patch('novaclient.client.Client', return_value=None)
    @mock.patch('neutronclient.neutron.client.Client', return_value=None)
    @mock.patch('swiftclient.client.Connection', return_value=None)
    def test__init_clients(self, swift, neutron, nova, sahara, glance,
                           m_session, m_auth):
        fake_session = mock.Mock()
        fake_auth = mock.Mock()
        m_session.return_value = fake_session
        m_auth.return_value = fake_auth

        self.base_scenario._init_clients()

        sahara.assert_called_with('1.1',
                                  session=fake_session,
                                  service_type='data-processing-local',
                                  sahara_url='http://sahara_host:8386/v1.1')
        swift.assert_called_with(
            auth_version='2.0', user='admin', key='nova', insecure=False,
            cacert='sahara_tests/unit/scenario/dummy.crt',
            tenant_name='admin', authurl='http://localhost:5000/v2.0')

        nova.assert_called_with('2', session=fake_session)
        neutron.assert_called_with('2.0', session=fake_session)
        glance.assert_called_with('2', session=fake_session)

        m_auth.assert_called_with(auth_url='http://localhost:5000/v3',
                                  username='admin',
                                  password='nova',
                                  project_name='admin',
                                  user_domain_name='default',
                                  project_domain_name='default')
        m_session.assert_called_with(
            auth=fake_auth,
            cert='sahara_tests/unit/scenario/dummy.crt', verify=True)

    @mock.patch('neutronclient.v2_0.client.Client.list_networks',
                return_value={'networks': [{'id': '2314'}]})
    @mock.patch('saharaclient.api.node_group_templates.'
                'NodeGroupTemplateManager.create',
                return_value=FakeResponse(set_id='id_ng'))
    def test__create_node_group_template(self, mock_del, mock_saharaclient):
        self.base_scenario._init_clients()
        self.assertEqual({'worker': 'id_ng', 'master': 'id_ng'},
                         self.base_scenario._create_node_group_templates())

    @mock.patch('neutronclient.v2_0.client.Client.list_networks',
                return_value={'networks': [{'id': '2314'}]})
    def test__create_node_group_template_bootfromvolume_apiv1(self, mock_del):
        self.base_scenario._init_clients()
        self.base_scenario.use_api_v2 = False
        for ng in self.base_scenario.testcase['node_group_templates']:
            ng['boot_from_volume'] = True
        with self.assertRaisesRegex(Exception, "^boot_from_volume is.*"):
            self.base_scenario._create_node_group_templates()

    @mock.patch('saharaclient.api.node_group_templates.'
                'NodeGroupTemplateManager.create',
                return_value=FakeResponse(set_id='id_ng'))
    @mock.patch('neutronclient.v2_0.client.Client.list_networks',
                return_value={'networks': [
                    {'id': '342'}
                ]})
    @mock.patch('neutronclient.v2_0.client.Client.create_security_group',
                return_value={'security_group': {'id': '213'}})
    @mock.patch('sahara_tests.scenario.clients.NeutronClient'
                '.add_security_group_rule_for_neutron',
                return_value='sg_name')
    @mock.patch('sahara_tests.scenario.clients.NeutronClient'
                '.delete_security_group_for_neutron',
                return_value=None)
    def test__create_security_group_uuid(self, mock_del, mock_add_rule,
                                         mock_sg, mock_neutron, mock_ng):
        self.base_scenario.network['public_network'] = (
            '692dcc5b-1205-4645-8a12-2558579ed17e')
        self.base_scenario._init_clients()
        for ng in self.base_scenario.testcase['node_group_templates']:
            ng['auto_security_group'] = False
        self.assertEqual({'master': 'id_ng', 'worker': 'id_ng'},
                         self.base_scenario._create_node_group_templates())

    @mock.patch('saharaclient.api.node_group_templates.'
                'NodeGroupTemplateManager.create',
                return_value=FakeResponse(set_id='id_ng'))
    @mock.patch('neutronclient.v2_0.client.Client.list_networks',
                return_value={'networks': [
                    {'id': '342'}
                ]})
    @mock.patch('neutronclient.v2_0.client.Client.create_security_group',
                return_value={'security_group': {'id': '213'}})
    @mock.patch('sahara_tests.scenario.clients.NeutronClient'
                '.create_security_group_for_neutron',
                return_value='sg_name')
    @mock.patch('neutronclient.v2_0.client.Client.create_security_group_rule',
                return_value=None)
    @mock.patch('neutronclient.v2_0.client.Client.delete_security_group',
                return_value=None)
    def test__create_security_group(self, mock_del, mock_create, mock_sg,
                                    mock_sgn, mock_list, mock_ng):
        self.base_scenario._init_clients()
        for ng in self.base_scenario.testcase['node_group_templates']:
            ng['auto_security_group'] = False
        self.assertEqual({'master': 'id_ng', 'worker': 'id_ng'},
                         self.base_scenario._create_node_group_templates())

    @mock.patch('sahara_tests.scenario.clients.NeutronClient.get_network_id',
                return_value='mock_net')
    @mock.patch('saharaclient.api.cluster_templates.'
                'ClusterTemplateManager.create',
                return_value=FakeResponse(set_id='id_ct'))
    def test__create_cluster_template(self, mock_ct, mock_neutron):
        self.base_scenario._init_clients()
        self.assertEqual('id_ct',
                         self.base_scenario._create_cluster_template())

    @mock.patch('saharaclient.api.images.ImageManager.get',
                return_value=FakeResponse(set_id='image'))
    @mock.patch('sahara_tests.scenario.clients.GlanceClient.get_image_id',
                return_value='mock_image')
    @mock.patch('saharaclient.api.clusters.ClusterManager.create',
                return_value=FakeResponse(set_id='id_cluster'))
    def test__create_cluster(self, mock_cluster_manager, mock_glance,
                             mock_image):
        self.base_scenario._init_clients()
        self.assertEqual('id_cluster',
                         self.base_scenario._create_cluster('id_ct'))

    @mock.patch('sahara_tests.scenario.clients.NeutronClient.get_network_id',
                return_value='mock_net')
    @mock.patch('saharaclient.api.base.ResourceManager._get',
                return_value=FakeResponse(
                    set_status=base.CLUSTER_STATUS_ACTIVE))
    def test__poll_cluster_status(self, mock_status, mock_neutron):
        self.base_scenario._init_clients()
        self.assertIsNone(
            self.base_scenario._poll_cluster_status('id_cluster'))

    @mock.patch('saharaclient.api.base.ResourceManager._get')
    def test_check_event_log_feature(self, mock_resp):
        self.base_scenario._init_clients()

        self.assertIsNone(self.base_scenario._check_event_logs(
            FakeCluster(True, [])))
        self.assertIsNone(self.base_scenario._check_event_logs(
            FakeCluster(False, [{'successful': True}])))

        with testtools.ExpectedException(exc.TempestException):
            self.base_scenario._check_event_logs(
                FakeCluster(False, [{'successful': False}]))

        with testtools.ExpectedException(exc.TempestException):
            self.base_scenario._check_event_logs(
                FakeCluster(False, [{'successful': None}]))

    @mock.patch('saharaclient.api.base.ResourceManager._update',
                return_value=FakeResponse(set_id='id_internal_db_data'))
    def test__create_internal_db_data(self, mock_update):
        self.base_scenario._init_clients()
        self.assertEqual('internal-db://id_internal_db_data',
                         self.base_scenario._create_internal_db_data(
                             'sahara_tests/unit/scenario/vanilla2_7_1.yaml'))

    @mock.patch('swiftclient.client.Connection.put_container',
                return_value=None)
    def test__create_swift_data(self, mock_swiftclient):
        self.base_scenario._init_clients()
        self.assertIn('swift://sahara-tests-',
                      self.base_scenario._create_swift_data())

    @mock.patch('swiftclient.client.Connection.put_container',
                return_value=None)
    def test__get_swift_container(self, mock_swiftclient):
        self.base_scenario._init_clients()
        self.assertIn('sahara-tests-',
                      self.base_scenario._get_swift_container())

    @mock.patch('saharaclient.api.base.ResourceManager._create',
                return_value=FakeResponse(set_id='id_for_datasource'))
    @mock.patch('swiftclient.client.Connection.put_container',
                return_value=None)
    @mock.patch('swiftclient.client.Connection.put_object',
                return_value=None)
    def test__create_datasources(self, mock_swiftcontainer, mock_swiftobject,
                                 mock_create):
        self.base_scenario._init_clients()
        self.assertEqual(('id_for_datasource', 'id_for_datasource'),
                         self.base_scenario._create_datasources(
                             self.job))

    @mock.patch('saharaclient.api.base.ResourceManager._create',
                return_value=FakeResponse(set_id='id_for_job_binaries'))
    @mock.patch('sahara_tests.scenario.clients.BotoClient.upload_data',
                return_value={})
    @mock.patch('sahara_tests.scenario.clients.BotoClient.create_bucket',
                return_value={'Location': 'foo'})
    @mock.patch('swiftclient.client.Connection.put_object',
                return_value=None)
    @mock.patch('swiftclient.client.Connection.put_container',
                return_value=None)
    def test__create_create_job_binaries(self, mock_swiftcontainer,
                                         mock_swiftobject,
                                         mock_create_bucket,
                                         mock_upload_bucket_data,
                                         mock_sahara_create):
        self.base_scenario._init_clients()
        self.assertEqual((['id_for_job_binaries'], []),
                         self.base_scenario._create_job_binaries(
                             self.job))

    @mock.patch('saharaclient.api.base.ResourceManager._create',
                return_value=FakeResponse(set_id='id_for_job_binary'))
    @mock.patch('sahara_tests.scenario.clients.BotoClient.create_bucket',
                return_value={'Location': 'foo'})
    @mock.patch('swiftclient.client.Connection.put_object',
                return_value=None)
    @mock.patch('swiftclient.client.Connection.put_container',
                return_value=None)
    @mock.patch('saharaclient.client.Client', return_value=FakeSaharaClient())
    def test__create_create_job_binary(self, mock_saharaclient,
                                       mock_swiftcontainer, mock_swiftobject,
                                       mock_create_bucket, mock_sahara_create):
        self.base_scenario._init_clients()
        self.assertEqual('id_for_job_binary',
                         self.base_scenario._create_job_binary(self.job.get(
                             'input_datasource')))

    @mock.patch('saharaclient.api.base.ResourceManager._create',
                return_value=FakeResponse(set_id='id_for_job'))
    def test__create_job(self, mock_client):
        self.base_scenario._init_clients()
        self.assertEqual('id_for_job',
                         self.base_scenario._create_job(
                             'Pig',
                             ['id_for_job_binaries'],
                             []))

    @mock.patch('sahara_tests.scenario.clients.SaharaClient.get_cluster_id',
                return_value='cluster_id')
    @mock.patch('sahara_tests.scenario.clients.SaharaClient.get_cluster',
                return_value=FakeCluster(ng=[]))
    @mock.patch('sahara_tests.scenario.base.BaseTestCase.check_cinder',
                return_value=None)
    @mock.patch('sahara_tests.scenario.clients.SaharaClient.get_job_status',
                return_value='KILLED')
    @mock.patch('saharaclient.api.base.ResourceManager._get',
                return_value=FakeResponse(set_id='id_for_run_job_get',
                                          job_type='Java',
                                          name='test_job'))
    @mock.patch('saharaclient.api.base.ResourceManager._create',
                return_value=FakeResponse(set_id='id_for_run_job_create'))
    @mock.patch('sahara_tests.scenario.base.BaseTestCase.'
                '_poll_cluster_status',
                return_value=None)
    @mock.patch('sahara_tests.scenario.base.BaseTestCase.'
                '_create_node_group_templates',
                return_value='id_node_group_template')
    @mock.patch('sahara_tests.scenario.base.BaseTestCase.'
                '_create_cluster_template',
                return_value='id_cluster_template')
    @mock.patch('sahara_tests.scenario.base.BaseTestCase._create_cluster',
                return_value='id_cluster')
    @mock.patch('sahara_tests.scenario.base.BaseTestCase._create_job',
                return_value='id_for_job')
    @mock.patch('sahara_tests.scenario.base.BaseTestCase._create_job_binaries',
                return_value=(['id_for_job_binaries'], []))
    @mock.patch('sahara_tests.scenario.base.BaseTestCase._create_datasources',
                return_value=('id_for_datasource', 'id_for_datasource'))
    @mock.patch('sahara_tests.scenario.base.BaseTestCase.check_verification')
    def test_check_run_jobs(self, mock_verification, mock_datasources,
                            mock_job_binaries, mock_job,
                            mock_node_group_template, mock_cluster_template,
                            mock_cluster, mock_cluster_status, mock_create,
                            mock_get, mock_client, mock_cinder, mock_get_cl,
                            mock_get_cluster_id):
        self.base_scenario._init_clients()
        self.base_scenario.create_cluster()
        self.base_scenario.testcase["edp_jobs_flow"] = [
            {
                "type": "Pig",
                "input_datasource": {
                    "type": "s3",
                    "source": "sahara_tests/scenario/defaults/edp-examples/"
                              "edp-pig/top-todoers/"
                              "data/input"
                },
                "output_datasource": {
                    "type": "hdfs",
                    "destination": "/user/hadoop/edp-output"
                },
                "main_lib": {
                    "type": "swift",
                    "source": "sahara_tests/scenario/defaults/edp-examples/"
                              "edp-pig/top-todoers/"
                              "example.pig"
                }
            }
        ]
        with mock.patch('time.sleep'):
            self.assertIsNone(self.base_scenario.check_run_jobs())
        self.assertIn("Job with id=id_for_run_job_create, name=test_job, "
                      "type=Java has status KILLED",
                      self.base_scenario._results[-1]['traceback'][-1])

    @mock.patch('sahara_tests.scenario.base.BaseTestCase._poll_cluster_status',
                return_value=None)
    @mock.patch('saharaclient.api.base.ResourceManager._get',
                return_value=FakeResponse(set_id='id_scale_get'))
    @mock.patch('saharaclient.api.base.ResourceManager._update',
                return_value=FakeResponse(set_id='id_scale_update'))
    def test_check_scale(self, mock_update, mock_get, mock_poll):
        self.base_scenario._init_clients()
        self.base_scenario.ng_id_map = {'vanilla-worker': 'set_id-w',
                                        'vanilla-master': 'set_id-m'}
        self.base_scenario.ng_name_map = {'vanilla-worker': 'worker-123',
                                          'vanilla-master': 'master-321'}
        self.base_scenario.cluster_id = 'cluster_id'
        self.assertIsNone(self.base_scenario.check_scale())

    @mock.patch('sahara_tests.scenario.clients.NeutronClient.get_network_id',
                return_value='mock_net')
    @mock.patch('saharaclient.api.base.ResourceManager._get',
                return_value=FakeResponse(set_status='Error',
                                          status_description=""))
    def test_errormsg(self, mock_status, mock_neutron):
        self.base_scenario._init_clients()
        with testtools.ExpectedException(exc.TempestException):
            self.base_scenario._poll_cluster_status('id_cluster')

    def test_get_nodes_with_process(self):
        self.base_scenario._init_clients()
        with mock.patch(
                'sahara_tests.scenario.clients.SaharaClient.get_cluster',
                return_value=FakeResponse(node_groups=[
                    {
                        'node_processes': ['test'],
                        'instances': ['test_instance']
                    }
                ])):
            self.assertEqual(
                ['test_instance'],
                self.base_scenario._get_nodes_with_process('test')
            )

        with mock.patch(
                'sahara_tests.scenario.clients.SaharaClient.get_cluster',
                return_value=FakeResponse(node_groups=[
                    {
                        'node_processes': 'test',
                        'instances': []
                    }
                ])):
            self.assertEqual(
                [], self.base_scenario._get_nodes_with_process('test'))

    def test_get_node_list_with_volumes(self):
        self.base_scenario._init_clients()
        with mock.patch(
                'sahara_tests.scenario.clients.SaharaClient.get_cluster',
                return_value=FakeResponse(node_groups=[
                    {
                        'node_processes': 'test',
                        'volumes_per_node': 2,
                        'volume_mount_prefix': 2,
                        'instances': [
                            {
                                'management_ip': 'test_ip'
                            }
                        ]
                    }
                ])):
            self.assertEqual(
                [{
                    'node_ip': 'test_ip',
                    'volume_count': 2,
                    'volume_mount_prefix': 2
                }], self.base_scenario._get_node_list_with_volumes())

    @mock.patch('sahara_tests.scenario.clients.SaharaClient.get_datasource')
    def test_put_io_data_to_configs(self, get_datasources):
        self.base_scenario._init_clients()
        get_datasources.side_effect = [
            mock.Mock(id='1', url="swift://cont/input"),
            mock.Mock(id='2', url="hdfs://cont/output")
        ]
        configs = {'args': ['2', "{input_datasource}",
                            "{output_datasource}"]}
        self.assertEqual({'args': ['2', 'swift://cont/input',
                                   'hdfs://cont/output']},
                         self.base_scenario._put_io_data_to_configs(
            configs, '1', '2'))

    @mock.patch('sahara_tests.scenario.base.BaseTestCase.addCleanup')
    @mock.patch('novaclient.v2.flavors.FlavorManager.create',
                return_value=FakeFlavor(flavor_id='created_flavor_id'))
    def test_get_flavor_id_anonymous(self, mock_create_flavor, mock_base):
        self.base_scenario._init_clients()
        self.assertEqual('created_flavor_id',
                         self.base_scenario._get_flavor_id({
                             "id": 'created_flavor_id',
                             "vcpus": 1,
                             "ram": 512,
                             "root_disk": 1,
                             "ephemeral_disk": 1,
                             "swap_disk": 1
                         }))

    @mock.patch('sahara_tests.scenario.base.BaseTestCase.addCleanup')
    @mock.patch('novaclient.v2.flavors.FlavorManager.create',
                return_value=FakeFlavor(flavor_id='created_flavor_id'))
    @mock.patch('novaclient.v2.flavors.FlavorManager.list',
                return_value=[FakeFlavor(flavor_id='existing_flavor_id',
                                         name='test-flavor')])
    def test_get_flavor_name_found(self, mock_list_flavor, mock_create_flavor,
                                   mock_base):
        self.base_scenario._init_clients()
        self.assertEqual('existing_flavor_id',
                         self.base_scenario._get_flavor_id({
                             'name': 'test-flavor',
                             "id": 'created_flavor_id',
                             "vcpus": 1,
                             "ram": 512,
                             "root_disk": 1,
                             "ephemeral_disk": 1,
                             "swap_disk": 1
                         }))

    @mock.patch('sahara_tests.scenario.base.BaseTestCase.addCleanup')
    @mock.patch('novaclient.v2.flavors.FlavorManager.create',
                return_value=FakeFlavor(flavor_id='created_flavor_id'))
    @mock.patch('novaclient.v2.flavors.FlavorManager.list',
                return_value=[FakeFlavor(flavor_id='another_flavor_id',
                                         name='another-flavor')])
    def test_get_flavor_id_not_found(self, mock_list_flavor,
                                     mock_create_flavor, mock_base):
        self.base_scenario._init_clients()
        self.assertEqual('created_flavor_id',
                         self.base_scenario._get_flavor_id({
                             'name': 'test-flavor',
                             "id": 'created_flavor_id',
                             "vcpus": 1,
                             "ram": 512,
                             "root_disk": 1,
                             "ephemeral_disk": 1,
                             "swap_disk": 1
                         }))

    @mock.patch('sahara_tests.scenario.base.BaseTestCase._run_command_on_node')
    def test_create_hdfs_data(self, mock_ssh):
        self.base_scenario._init_clients()
        output_path = '/user/test/data/output'
        self.assertEqual(output_path,
                         self.base_scenario._create_dfs_data(None, output_path,
                                                             None, 'hdfs'))
        input_path = ('sahara_tests/scenario/defaults/edp-examples/edp-pig/'
                      'trim-spaces/data/input')
        with mock.patch(
            'sahara_tests.scenario.clients.SaharaClient.get_cluster',
            return_value=FakeResponse(node_groups=[
                {
                    'node_processes': ['master', 'namenode'],
                    'instances': [{
                        'management_ip': 'test_ip'
                    }]
                }])):
            self.assertIn('/user/test/data-', (
                self.base_scenario._create_dfs_data(input_path, None,
                                                    'test', 'hdfs')))

    @mock.patch('saharaclient.api.base.ResourceManager._get',
                return_value=FakeResponse(
                    set_status=base.CLUSTER_STATUS_ACTIVE,
                    verification={'verification': {
                        'status': 'GREEN',
                        'cluster_id': 'id_cluster'
                    }}))
    @mock.patch('saharaclient.api.clusters.ClusterManager.verification_update')
    @mock.patch('sahara_tests.scenario.base.BaseTestCase.'
                'check_feature_available', return_value=True)
    def test_check_verification_did_not_start(self, mock_feature,
                                              mock_verification,
                                              mock_get_status):
        self.base_scenario._init_clients()
        self.assertIsNone(self.base_scenario.check_verification('id_cluster'))

    @mock.patch('saharaclient.api.base.ResourceManager._get',
                return_value=FakeResponse(
                    set_status=base.CLUSTER_STATUS_ACTIVE))
    @mock.patch('saharaclient.api.clusters.ClusterManager.verification_update')
    @mock.patch('sahara_tests.scenario.base.BaseTestCase.'
                'check_feature_available', return_value=True)
    @mock.patch('sahara_tests.scenario.base.BaseTestCase._get_health_status',
                return_value='GREEN')
    def test_verification_start(self, mock_status, mock_feature,
                                mock_verification, mock_get_status):
        self.base_scenario._init_clients()
        self.assertIsNone(self.base_scenario.check_verification('id_cluster'))

    @mock.patch('saharaclient.api.base.ResourceManager._get',
                return_value=FakeResponse(
                    set_status=base.CLUSTER_STATUS_ACTIVE))
    @mock.patch('saharaclient.api.clusters.ClusterManager.verification_update')
    def test_verification_skipped(self, mock_verification, mock_get_status):
        self.base_scenario._init_clients()
        self.assertIsNone(self.base_scenario.check_verification('id_cluster'))
