=========================
Pig StringCleaner Example
=========================

Overview
--------
This is an (almost useless) example of Pig job which uses a custom UDF (User
Defined Function).

- ``StringCleaner.java`` is a Pig UDF which strips some characters from the
  input.
- ``example.pig`` is the main Pig code which uses the UDF;


Compiling the UDF
-----------------

To build the jar, add ``pig`` to the classpath.

    $ cd src
    $ mkdir build
    $ javac -source 1.6 -target 1.6 -cp /path/to/pig.jar -d build StringCleaner.java
    $ jar -cvf edp-pig-stringcleaner.jar -C build/ .

Running from the Sahara UI
--------------------------

The procedure does not differ from the usual steps for other Pig jobs.

Create a job template where:
- the main library points to the job binary for ``example.pig``;
- additional library contains the job binary for ``edp-pig-udf-stringcleaner.jar``.

Create a job from that job template and attach the input and output data
sources.
