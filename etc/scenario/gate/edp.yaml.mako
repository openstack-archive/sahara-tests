edp_jobs_flow:
  fake:
    - type: Pig
      input_datasource:
        type: swift
        source: edp-examples/edp-pig/cleanup-string/data/input
      output_datasource:
        type: hdfs
        destination: /user/hadoop/edp-output
      main_lib:
        type: swift
        source: edp-examples/edp-pig/cleanup-string/example.pig
      additional_libs:
        - type: swift
          source: edp-examples/edp-pig/cleanup-string/edp-pig-udf-stringcleaner.jar
  spark_pi:
    - type: Spark
      main_lib:
        type: database
        source: edp-examples/edp-spark/spark-pi.py
      configs:
        edp.java.main_class: main
      args:
        - 2
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
