edp_jobs_flow:
  spark_wordcount_s3:
    - type: Spark
      input_datasource:
        type: s3
        source: edp-examples/edp-spark/sample_input.txt
      output_datasource:
        type: swift
        destination: edp-output
      main_lib:
        type: swift
        source: edp-examples/edp-spark/spark-wordcount.jar
      configs:
        edp.java.main_class: sahara.edp.spark.SparkWordCount
        edp.spark.adapt_for_swift: true
        fs.swift.service.sahara.username: ${os_username}
        fs.swift.service.sahara.password: ${os_password}
        fs.s3a.access.key: ${s3_accesskey}
        fs.s3a.secret.key: ${s3_secretkey}
        fs.s3a.endpoint: ${s3_endpoint}
        fs.s3a.connection.ssl.enabled: ${s3_endpoint_ssl}
        fs.s3a.path.style.access: ${s3_bucket_path}
      args:
        - '{input_datasource}'
        - '{output_datasource}'
