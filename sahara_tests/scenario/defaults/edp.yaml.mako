edp_jobs_flow:
  pig_job:
    - type: Pig
      input_datasource:
        type: swift
        source: edp-examples/edp-pig/cleanup-string/data/input
      output_datasource:
        type: swift
        destination: edp-output
      main_lib:
        type: swift
        source: edp-examples/edp-pig/cleanup-string/example.pig
      additional_libs:
        - type: swift
          source: edp-examples/edp-pig/cleanup-string/edp-pig-udf-stringcleaner.jar
  mapreduce_job:
    - type: MapReduce
      input_datasource:
        type: swift
        source: edp-examples/edp-pig/trim-spaces/data/input
      output_datasource:
        type: hdfs
        destination: /user/hadoop/edp-output
      additional_libs:
        - type: database
          source:  edp-examples/edp-mapreduce/edp-mapreduce.jar
      configs:
        mapred.map.class: org.apache.oozie.example.SampleMapper
        mapred.reduce.class: org.apache.oozie.example.SampleReducer
        mapreduce.framework.name: yarn
  mapreduce_streaming_job:
    - type: MapReduce.Streaming
      input_datasource:
        type: swift
        source: edp-examples/edp-pig/trim-spaces/data/input
      output_datasource:
        type: hdfs
        destination: /user/hadoop/edp-output
      configs:
        edp.streaming.mapper: /bin/cat
        edp.streaming.reducer: /usr/bin/wc
  java_job:
    - type: Java
      additional_libs:
        - type: database
          source: edp-examples/hadoop2/edp-java/hadoop-mapreduce-examples-2.6.0.jar
      configs:
       edp.java.main_class: org.apache.hadoop.examples.QuasiMonteCarlo
      args:
        - 10
        - 10
  hive_job:
    - type: Hive
      main_lib:
        type: swift
        source: edp-examples/edp-hive/script.q
      input_datasource:
        type: hdfs
        source: edp-examples/edp-hive/input.csv
      output_datasource:
        type: hdfs
        destination: /user/edp-output
  spark_pi:
    - type: Spark
      main_lib:
        type: database
        source: edp-examples/edp-spark/spark-pi.py
      configs:
        edp.java.main_class: main
      args:
        - 4
  spark_wordcount:
    - type: Spark
      input_datasource:
        type: swift
        source: edp-examples/edp-spark/sample_input.txt
      output_datasource:
        type: swift
        destination: edp-output
      main_lib:
        type: database
        source: edp-examples/edp-spark/spark-wordcount.jar
      configs:
        edp.java.main_class: sahara.edp.spark.SparkWordCount
        edp.spark.adapt_for_swift: true
        fs.swift.service.sahara.username: ${os_username}
        fs.swift.service.sahara.password: ${os_password}
      args:
        - '{input_datasource}'
        - '{output_datasource}'
  mapr_pig_job:
    - type: Pig
      input_datasource:
        type: maprfs
        source: edp-examples/edp-pig/cleanup-string/data/input
      output_datasource:
        type: maprfs
        destination: /user/hadoop/edp-output
      main_lib:
        type: swift
        source: edp-examples/edp-pig/cleanup-string/example.pig
      additional_libs:
        - type: swift
          source: edp-examples/edp-pig/cleanup-string/edp-pig-udf-stringcleaner.jar
  mapr:
    - type: MapReduce
      input_datasource:
        type: maprfs
        source: edp-examples/edp-pig/trim-spaces/data/input
      output_datasource:
        type: maprfs
        destination: /user/hadoop/edp-output
      additional_libs:
        - type: database
          source:  edp-examples/edp-mapreduce/edp-mapreduce.jar
      configs:
        mapred.mapper.class: org.apache.oozie.example.SampleMapper
        mapred.reducer.class: org.apache.oozie.example.SampleReducer
    - type: MapReduce.Streaming
      input_datasource:
        type: maprfs
        source: edp-examples/edp-pig/trim-spaces/data/input
      output_datasource:
        type: maprfs
        destination: /user/hadoop/edp-output
      configs:
        edp.streaming.mapper: /bin/cat
        edp.streaming.reducer: /usr/bin/wc
    - type: Java
      additional_libs:
        - type: database
          source: edp-examples/hadoop2/edp-java/hadoop-mapreduce-examples-2.6.0.jar
      configs:
       edp.java.main_class: org.apache.hadoop.examples.QuasiMonteCarlo
      args:
        - 10
        - 10
