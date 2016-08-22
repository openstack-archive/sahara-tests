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
