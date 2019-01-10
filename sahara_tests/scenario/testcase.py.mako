from sahara_tests.scenario import base

% for testcase in testcases:
    ${make_testcase(testcase)}
% endfor

<%def name="make_testcase(testcase)">
class ${testcase['class_name']}TestCase(base.BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super(${testcase['class_name']}TestCase, cls).setUpClass()
        cls.credentials = ${credentials}
        cls.network = ${network}
        cls.testcase = ${testcase}
        cls.report = ${report}
        cls.results_dir = '${results_dir}'
        cls.default_templ_dir = '${default_templ_dir}'
        cls.use_api_v2 = ${use_api_v2}

    def test_plugin(self):
        self.create_cluster()
    % for check in testcase['scenario']:
        from sahara_tests.scenario.custom_checks import check_${check}
        check_${check}.check(self)
    % endfor
</%def>
