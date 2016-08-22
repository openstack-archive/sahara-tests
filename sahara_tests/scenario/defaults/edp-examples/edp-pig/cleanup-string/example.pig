A = load '$INPUT' using PigStorage() as (lines: chararray);
B = foreach A generate org.openstack.sahara.examples.pig.StringCleaner(lines);
store B into '$OUTPUT' USING PigStorage();
