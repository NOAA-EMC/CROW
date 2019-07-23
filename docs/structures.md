Structures
========================

YAML in general

YAML(acronym of “YAML Ain't Markup Language”) is a human-readable data serialization language. Native YAML encodes data types that are specifically suitable for configuration. In this application, an enhanced format called CROW-YAML is developed along with a series of advanced functionalities and data types to support the configuration of the workflows of NOAA.

The CROW package has two-way conversion functions between YAML text files and configuration suite in memory. The configuration suite is essentially a python dictionary with all configuration settings. The settings are then parsed into config files, rocoto XML and ecFlow suite.

Processing of YAML files

As a serialization language, YAML is extremely suitable to handle configuration practice because of it’s keyword-free syntax, highly human-readable nature, and the conveniency of handling multiple types of value within a single object. 

This data structure is then read by a Python YAML toolbox called PyYAML. The primary function of PyYAML is two-way conversion between a YAML text file and a python object. Please note that YAML can be read by all major programming languages (Perl, Ruby, C++, Java…… ) when proper libraries are provided. Python is chosen for this project because it’s growing popularity in NCEP.

CROW YAML is developed on top of PyYAML with the addition of several customized data types. User-defined data type is named alpha-numerically with “!” at the beginning when calling. CROW defines several of these to handle calculations, conditionals, templates, times, dependencies, and some others.



Features:
Only once. Though not recommended, CROW enables users to specify a certain variable and override it at a later stage. But, only one value of a certain variable could be passed into the targeted workflow that is generated.
All or none. CROW always reads all YAML files at one time. This design helps ensure consistency within the Configuration Suite and Workflow Suite.
Diagnosable. In CROW, the experiment directory has effectively become a “checkpoint” for the configuration. This helps minimize human error and increase accountability, comparing with manually editing throughout experiment directory.
    
This file will be read by crow.config and become a eval_dict object of python. There are two sections in the eval_dict created, original contents are stored in _child and calculated values are stored in _cache.

CROW based workflow suite

CROW is a python based toolbox driven by a series of shell based utility scripts. In CROW-enabled modeling systems, top level directory /workflow is the designated place to start working with workflow generation. Under this directory locates the sub-repository CROW. Users need to perform a “git submodule” command to pull CROW from the cloud. Outside CROW repository, a user.yaml file and a case/ directory is needed to accommodate user and case settings. In addition to these, CROW needs a set of background files to fulfill its functionality. These files are stored in workflow/defaults; workflow/workflow; workflow/runtime; workflow/platforms and /schema.

As stated before, CROW uses a two-step approach to generate a workflow. The first step is called Configuration. In this step, CROW will detect the running platform and read in all YAML files to make sure all required variables are properly set. If no problem occurs, a Configuration Suite will be generated. The Configuration Suite is a virtual object in the form of python ecal_dict, which is essentially a database which only exists in memory. In the end, CROW will rewrite all input YAMLs into experiment directory, which is created in the beginning of this step, and parse all configuration variables to config files into the experiment directory.

Namely, a configuration suite contains all configuration information of a given experiment, including default settings (clock, alarm) and most importantly, a series of tasks with dependencies between each other. A suite can be defined over one or more cycles, while each task has a section to define which cycle it will run.


CROW Step 1, Configuration
Flag-shaped boxes are text files; Circular bins are python objects;
Yellow: User input files;
Red: Background configuration files
Green: Output files;



In the second step, named Generation, CROW will read in all YAML files and generate the Configuration Suite again, while also populate all tasks, along with suite default settings, onto designated cycles to generate a Workflow Suite, with choice of Rocoto or ecFlow as workflow manager. 


CROW Step 2, Generation
Flag-shaped boxes are text files; Circular bins are python objects;
Yellow: User input files;
Red: Background configuration files
Green: Output files;


The basic component of a CROW configuration suite is called a task. In a workflow, a task is a single element or step of the modeling system providing a certain functionality by a set of scripts (For example: gdasefcs01). Inside CROW toolbox, a task is represented by python objects. Most tasks are associated with a J-Job script which handles submission of a supercomputing job card, with specific resource requests (time, cpu, memory ...). Some tasks come as an array called a “taskarray”, where multiple tasks performing the same functionality are grouped together (ie, gfs_post_XX, enkf_forecast_XX …..).  Tasks will be instantiated as “jobs” when the workflow suite is generated and submitted to the workflow manager (For example: gdasefcs01 at 00 cycle and 06 cycle are two distinct jobs, but are derivatives of the same task gdasefcs01).


Fig 3. Detailed explanation of how tasks are defined will be given later

Example of task object creation: 

This is what has been defined in task_schema (rocoto section) :
task_schema: &task_schema !Template
          Rocoto:                    # Variable name
            description: >-            # Short description
                  XML to insert in the task definition, excluding the task tag
                  itself, and the dependencies.
            type: string                # Variable type
            stages: [ execution ]            # Validation stage
          rocoto_command:
            description: >-
Command to execute for this task when run in rocoto.  This is inserted into the rocoto command tag for the task.
            type: string
            stages: [ execution ]
…(More variables)...
This is what has been inherited and defined in task_template, only the rocoto parts are shown:
task_template: &task_template
Template: *task_schema        # Load task_schema
            Rocoto: !expand |            # “|” for multi-line string
# actual string with {} to be filled by other variables
            <command>sh -c '{rocoto_command}'</command>
            {partition.scheduler.rocoto_accounting(
                partition_specification,default_accounting,accounting,
              jobname=task_path_var,
                outerr=rocoto_log_path,
                partition=partition.specification)}
            rocoto_command: !expand >-    # actual string with {}
             {rocoto_load_modules} ;
             {rocoto_config_source} ;
             {J_JOB_PATH}/{J_JOB}
<envar><name>CDATE</name><value><cyclestr>@Y@m@d@H</cyclestr></value></envar>
            …(More lines of rocoto contents like the line above)...
        …(More variables)...

This is what has been inherited and defined in forecast_task_template, 
forecast_task_template: &exclusive_task_template    # This is a task template
      <<: *task_template                    # It loads this template
      partition: !calc doc.accounting.exclusive_partition    # Running on this partition
      default_accounting: !calc partition.exclusive_accounting_ref
                                # default accounting 
      J_JOB: !expand '{task_path_list[-1].upper()}'    # interface for J_Job
      task_type: forecast                    # sticker
    
This is an actual task in the YAML configuration suite:
            jgdas_forecast_high: !Task                # This is a task
        <<: *forecast_task_template            # It loads this template
Trigger: !Depend ( up.analysis.jgdas_analysis_high ) | ~ suite.has_cycle('-6:00:00')            # This is the dependecies
resources: !calc partition.resources.run_gdasfcst    
# This is resource request
J_JOB: JGLOBAL_FORECAST        # This is the associated J-Job

This is the task in Rocoto XML generated from CROW:

  <task name="gdas.forecast.jgdas_forecast_high" maxtries="5">
        <command>sh -c ' source $HOMEgfs/ush/load_fv3gfs_modules.sh exclusive ; module list ; source $EXPDIR/config.base ; $HOMEgfs/jobs/JGLOBAL_FORECAST'</command>
        <queue>&QUEUE;</queue>
        <account>&CPU_PROJECT;</account>
        <jobname>gdas.forecast.jgdas_forecast_high</jobname>
        <join><cyclestr>&LOG_DIR;/@Y@m@d@H/gdas.forecast.jgdas_forecast_high.log</cyclestr></join>

        <walltime>0:30:00</walltime>
        <memory>1024M</memory>
        <nodes>1:ppn=4+2:ppn=3</nodes>

        <envar><name>CDATE</name><value><cyclestr>@Y@m@d@H</cyclestr></value></envar>
        <envar><name>PDY</name><value><cyclestr>@Y@m@d</cyclestr></value></envar>
        <envar><name>cyc</name><value><cyclestr>@H</cyclestr></value></envar>
        <envar><name>EXPDIR</name><value>&EXPDIR;</value></envar>
        <envar><name>DUMP</name><value>gdas</value></envar>
        <envar><name>RUN_ENVIR</name><value>emc</value></envar>
        <envar><name>HOMEgfs</name><value>&HOMEgfs;</value></envar>
        <envar><name>HOMEobsproc_network</name><value>&HOMEobsproc_network;</value></envar>
        <envar><name>HOMEobsproc_global</name><value>&HOMEobsproc_network;</value></envar>
        <envar><name>HOMEobsproc_prep</name><value>&HOMEobsproc_prep;</value></envar>
        <envar><name>job</name><value>jgdas_forecast_high_<cyclestr>@H</cyclestr></value></envar>


        <dependency>
              <or>
                    <taskdep task="gdas.analysis.jgdas_analysis_high"/>
                    <not>
                          <cycleexistdep cycle_offset="-06:00:00"/>
                    </not>
              </or>
        </dependency>
  </task>

Fig 4. Relationship between Configuration Suite and Workflow Suite

At this moment, configuration settings of each individual task are still coming from the corresponding config.xx files which is then linked to task. The purpose of this design is to make the transition easier for users of legacy configuration system. 



User Input Files
Format

The YAML files that require user inputs are all formatted in a classical and intuitive “Name: Value” convention. Python-style indentation rule is applied to differentiate multiple levels of variable sections. Top level named is “case” for case file; while “user_places” and “accounting” is used for user file.  Lower levels of contents include required and optional subsections. Order does not matter. 



case:
fv3_settings:
            CASE: C768
            LEVS: 65

          fv3_enkf_settings:
            CASE: C384

         ……

User file 

user.yaml

This file contains user-specific information of a given computing platform. Two sections “user_places” and “accounting” are included.

A template of this file named “user.yaml.default” is included in the repository under workflow/. Users need to make their own “user.yaml” by modifying the values within the template when running CROW for the first time. 

user_places:
This section is of the same structure as “places” in case.yaml. The intention is to include settings that are more connected to the user other than the experiment. Such variables are marked red in the list. However, the user has the freedom to put all these variables into either one. When a certain variable get specified in both files, the one in this section will overwrite the one within case.yaml.

accounting:
This section is designed to accommodate settings of supercomputer account and queue information.  





Case file 

[case name].yaml 

This file serves as the central place to configure the experiment parameters, located under /workflow/cases. Configurable variables are categorized by “group” for better handling and indexing. Complete list of variables for each group are given in the Appendix.

case name is a required argument of setup_case.sh. When executed, the program will look for case name is workflow/cases directory to match the correct case file. A user may provide the full name of the yaml file as well (e.g. case_name.yaml), the system can handle both.

“Default value: None” here means that no “group level” default values provided. But most of the variables still have an “individual” default value defined in the schema. Detail about the “default system” will be discussed later in the /default and /schema section.

fv3_settings: Define spatial/vertical resolution and various physics 
parameters for deterministic and ensemble forecast jobs.
    Template: fv3_settings_template
Default values: None

fv3_gfs_settings: settings for gfs (long forecast) model
    Template: fv3_settings_template
Default values: None

fv3_enkf_settings: settings for DA ensemble forecast
    Template: fv3_settings_template
Default values: fv3_enkf_defaults

fv3_gdas_settings: settings for DA deterministic forecast
    Template: fv3_settings_template
    Default values: None

For all four sections above, same variable list are provided. The gfs, enkf and gdas settings will inherit “fv3_settings” if not specified separately. 


schedvar: Scheduler-related variables. 
    Template: schedvar_schema
    Default: schedvar_defaults

gfs_output_settings: Model output settings
    Template: gfs_output_settings_template
    Default: gfs_output_settings_defaults

data_assimilation: Data assimilation configuration
    Template: data_assimilation_template
    Default: None

post: Post-processing configuration
    Template: post_schema
    Default: None

downstream: Switches for turning on/off downstream jobs
    Template: downstream_schema
    Default: downstream_defaults

places: Settings of paths. Also need to specify which workflow files is used to create the final workflow.
    Template: places_schema
    Default: default_places

nsst: 
Near Sea Surface Temperature scheme settings.
exclusive_resources, shared_resources, service_resources: Resource specifications, default settings in platform file.
    Template: nsst_schema
    Default: None

settings: general settings, like SDATE, EDATE and if “four cycle mode” will be used. 
    Template: settings_schema
    Default: default_settings



archiving: Settings for archiving data
Template: archive_settings_template
Default: None

Suite_overrides: Overriding values for the entire suite. No template is given.

Utility scripts: 

Three most important utility scripts for the CROW system, setup_case.sh, make_rocoto_xml_for.sh and make_ecflow_file_for.sh, are already discussed in the section above. There are several additional scripts come with the package for various functionalities.

eclipse_main.py

Usage: python3.6 eclipse_main.py

This script is a python-based version of the setup_case.sh. The purpose of this version is to provide the conveniency of launching IDE projects (ie: Eclipse) since most of them only support projects with only one language inside. It will do the following things: 
Validate platform;
Set up COMROT directory under ptmp location, which is typically specified in user.yaml; 
Set up experiment directory under PROJECT_DIR location, which is typically specified inside user.yaml; 
Create a configuration suite by reading all YAML files; A configuration suite is a python dictionary containing all configuration information. This suite is for validation and config file writing purpose and will only exist in memory.
Write out all YAML files and config files into experiment directory.


ecflow_main.py / rocoto_main.py

Usage: python3.6 eclipse_main.py
            python3.6 rocoto_main.py

This file is the python equivalent to “make_ecflow_file_for.sh” / “make_rocoto_file_for.sh” as the entry point of “generation” step for ecflow or rocoto workflow generation. 

worktools.py

This script is the central place to put top-level python functions regarding the handling of configuration definition documents and setting up the workflow. 

Background Files
Config

This directory stores the templates of all config files. For most modeling systems, it is usually a direct copy of “parm/config” directory. 

Config files are bash shell scripts named “config.XXX” while “XXX” usually stands for a specific workflow task (example: config.fcst; config.post). These files store configurable variables for job “XXX” for later use in J-Jobs and ex-scripts. In addition to that, there are config.base and config.resource for general settings and resource allotment. When the model runs, each J-Job script will read in one or several of these files.



platform

This directory stores designated YAML files for each supported computing platform. For a given platform that supports the target workflow, the following parameters are defined:

Evaluate: this must be "false" to ensure disk space availability logic is not run unless this file is for the current platform.
name: for machine name.
detect: The detect criteria (like top level file structure)
public_release_ics: location of input conditions that have been prepared for the public release
CHGRP_RSTPROD_COMMAND: rstprod data command.
NWPROD: location of NCEP operational directory.
DMPDIR: location of the global dump data
RTMFIX: location of the CRTM fixed data files used by the GSI data assimilation
BASE_GIT: git command path.
partitions: A comprehensive subsection, some machine comes with partitions like rdhpcs-jet. Resource allocation by partition are specified here.
    (partition detail)
Least_used_temp: return the least used tmp directory.


workflow


This directory stores different type of workflow layouts associated with a certain modeling system. For example, cycled vs forecast-only for Global Workflow. In each workflow file, a sequence of tasks, or family of tasks, are given in an orderly manner. Job dependencies are also addressed in this file.

schema


This directory serves as a template for the configurations system for a given workflow. For each of the [case section].yaml files within this directory, each file gives all possible values for a certain section of the workflow. 

The schema/task.yaml sets up task interfaces and defines a template for tasks at the top level. After this step, workflow/runtime/task.yaml will implement all these interfaces (ie, “ecf_file”, “rocoto_command”... ) with actual content regarding workflow manager information, which is then instantiated /subclassed in the actual workflow. This process can be viewed as a practice of class inheritance in object-oriented programming.

Fig 3. Detailed explanation of how tasks are defined will be given later


runtime


This is the section for a series of task templates, as together with a series of suite default sections of rocoto and ecFlow. For example, templates for the rocoto “header” section
  
suite.yaml: Defines virtual object “suite_default” which represents utilities and  common sections which are shared through the entire workflow. 


defaults

This directory stores default value for each part of the workflow. Comparing to the default values defined in /schema, this directory focuses on “group” default grouped by categories. These default values, if defined, will overwrite default values in schema. This section is organized in “group”s which is also housing all customized variables in the case file. Adding this section make configuration more manageable. 

Fig 4. Overriding sequence, values of config variables



Files:

defaults/case.yaml


This file has the top-level logic to merge other YAML data structures into the document-level settings. It merges the contents of the case files, default files, platform file, and everywhere else, and applies any validation from the schema/ directory. This file should also be the first file to begin with when trying to build CROW for a new modeling system.

defaults/downstream.yaml


This is a list of YES/NO switch to decide whether a downstream job should be included or not.

defaults/fv3_enkf.yaml


This is the default settings of fv3 model and enkf mechanics.

defaults/gfs_output_settings.yaml


This file contains settings specific to model output of GFS.

defaults/places.yaml


This file is designated place to put paths. For example the home directory of GFS model and home directory of CROW.

defaults/resources.yaml

This file stores default resource settings (number of cpu, length of time...) for each of the tasks in the workflow.

defaults/settings.yaml


This file is for general settings of global-workflow.

Testing 

Unit test and regression test are provided within the CROW package to help streamlining future development of the package. Unit tests focus on individual functions, while regression test proves if the output could be reproduced with updated code. Like the CROW package itself, python 3.6 is a requirement to run these tests ( and to perform develop works for CROW package )

Unit test: 
Enter the unit test directory: 
cd tests/unittests/slurm/
Execution command: 
sh run_tests.sh

Sample output: 
test_AprunCrayMPI_big (test_SrunMPI.TestAprunCrayMPI) ... INFO:root:assertions not set yet
ok
test_AprunCrayMPI_max_ppn (test_SrunMPI.TestAprunCrayMPI) ... INFO:root:assertions not set yet
ok
test_FirstMax (test_exampleConfig.TestExampleConfig) ... ok
test_FirstTrue (test_exampleConfig.TestExampleConfig) ... ok
…...


Unit test is done to ensure that all functions are in place and performs as designed. This test should be conducted after porting to a new platform, or working with a new version of the corresponding workflow (ie, global-workflow). 

Regression test:
Enter the regression test directory:
cd tests/regtest/
Execution command: 
python3 regtest.py

Sample output:
diff /scratch4/NCEPDEV/global/noscrub/Jian.Kuang/global-workflow/workflow/CROW/tests/test_data/regtest/cache/expdir/regtest_tmp/../../../control/defs/regtest_tmp /scratch4/NCEPDEV/global/noscrub/Jian.Kuang/global-workflow/workflow/CROW/tests/test_data/regtest/cache/expdir/regtest_tmp/../../defs/regtest_tmp
Differing files : ['regtest_tmp_2016021000.def']

diff /scratch4/NCEPDEV/global/noscrub/Jian.Kuang/global-workflow/workflow/CROW/tests/test_data/regtest/cache/expdir/regtest_tmp/../../../control/expdir/regtest_tmp /scratch4/NCEPDEV/global/noscrub/Jian.Kuang/global-workflow/workflow/CROW/tests/test_data/regtest/cache/expdir/regtest_tmp/../../expdir/regtest_tmp
Identical files : ['_main.yaml', 'case.yaml', 'config.anal', 'config.fcst', 'config.post', 'config.prep', 'names.yaml', 'platform.yaml', 'user.yaml', 'workflow.yaml']
Differing files : ['config.base', 'static_locations.yaml', 'workflow.crontab', 'workflow.xml']
Common subdirectories : ['config', 'defaults', 'runtime', 'schema']

CROW regression test is essentially a repeatability test for workflow generation process. This test should be done before committing any changes to the CROW master branch.

