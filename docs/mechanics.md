Mechanism
============

The CROW toolbox utilizes the same two-step, Configuration + Generation approach, as the “setup experiment → setup workflow” concept of the legacy global workflow. This approach was taken in order to better serve users of the legacy global workflow and shorten the learning curve as much as possible as they migrate to this new method of instantiating workflows. The figure below shows the flow of the CROW configuration and generation approach to generate a workflow, in this case a model experiment.

This section will give a detailed explanation of the process of workflow creation as well as the scripts involved, and compare it with legacy configuration process. It also gives preliminary introduction of the input files which meets the needs of most general users.

![Figure 3. CROW flowchart](/image/img3.jpg)

 - Gray arrows in this chart indicates the flow of configuration information. 
 - Round-cornered boxes are ASCII files at various stages, while diamond-shapes are scripts run by the user. 
 - Yellow color indicates places for user input, while dark green boxes are the final products.

For general users, the major difference with the legacy workflow system is that, instead of having users manually edit each config, CROW designates central places to put configuration parameters. The files that require user input are the (1) user file and (2) case file. They are highly templated text files storing user information and high-level configuration settings of each experiment. Detailed description and formatting will be discussed in “Structures” section .

After the user input stage are validation and setup stages handled internally by the toolbox. (1) The inputted user information (user file) and experiment design (case file) are validated against known allowed values built in by the developers of the particular system (i.e. model). (2) The output folders (e.g. COM directory) are established and populated with initial input data (if designed). (3) The workflow files are built and placed in your main experiment directory (e.g. xml file for Rocoto or suite definition files for ecFlow).

1. User input stage
--------------------

Set up user and case files
User file

The “user file” is a text file containing user specific information like their HPC account code. The user will find a default one that they should start with called “user.yaml.default” under /workflow. Make a copy called “user.yaml”:

> cp user.yaml.default user.yaml

...and modify as needed. 

Required settings in default user.yaml [user.yaml.default]: The “!error” contents are error messages that will pop up when the corresponding field is missing.

user_places: &user_places
    EXPROOT: !error Please select a project directory.
accounting: & accounting
    cpu_project: !error What accounting code do I use to submit jobs? # ie.: global
    hpss_project: !error Where do I put data on HPSS?   # ie.: emc-global
User file example: [user.yaml]

user_places: &user_places
EXPROOT: /mnt/lfs3/projects/hfv3gfs/
accounting: & accounting
  		cpu_project: hfv3gfs 
  		hpss_project: emc-global

All other settings allowed in the user file have defaults and may be left commented out. EXPROOT, cpu_project, and hpss_project are the only required modifications because there are no default values for these variables. Replace or comment out the !error messages and insert the needed values.

 - EXPROOT - location where experiment directory will be created, needs to be a place where user has write access.
 - cpu_project - the user’s account code to submit supercomputer job (e.g. global)
 - hpss_project - the user’s HPSS group for archival (e.g. emc-global)

More variables can be defined in this section. In general, two categories of variables could be defined in this file. Detailed explanation of this file is discussed in the “Structure” section.

The following list contains frequently included variables in user.yaml:

 - User_email = user email address where auto-generated status emails are sent to. For example, the crontab email address. [Optional]

 - LONG_TERM_TEMP = Temporary area that is scrubbed less often (can be the same as ROTDIR). If left commented out the toolbox will determine the long term temporary space with the most room at setup time. The location options for short term space are built into toolbox by developers when ported to HPC. Recommend leaving commented out.


 - SHORT_TERM_TEMP = Temporary area that is scrubbed quickly (can be the same as DATAROOT) and which is used at runtime by jobs. If left commented out the toolbox will determine the short term temporary space with the most room at setup time. The location options for short term space are built into toolbox by developers when ported to HPC. Recommend leaving commented out.


 - ROTDIR = ROTating DIRectory, where model inputs and outputs will reside. Main output directory. Subdirectories are organized in $RUN.$PDY/$HOUR convention (e.g. gdas.2019021400/00, gfs.2019021400/06 ). At this moment, this is usually the same value as LONG_TERM_TEMP.

 - DATAROOT = Run-time directory. Subdirectories are created for each job. All input files, restart files, and executables will be soft-linked to the corresponding subdirectory under this place. Namelists and temporary outputs will be generated here. When a job has finished successfully, outputs will either be copied or linked to ROTDIR. Usually put in SHORT_TERM_TEMP.

 - ICSDIR = Path to your generated initial conditions on disk, if created beforehand.

 - ecflow_machine = Server for ecFlow (WCOSS only currently). This variable only makes sense when running ecFlow-driven workflow.

 - *_partition = Partition to run on. Some supercomputers (e.g. RDHPCS-jet) have “partitions”, which are subsets of computing resources. Specifying these could enable users to run a job on certain partitions based on the feature of the given job (extensive computing? Large Memory? … ).





Case file

The “case file” is a text file containing configuration settings for your experiment (a.k.a. experiment design). The format of the case file is straightforward, as a section / subsection / key / value structure. Python-like indentation rules have to be followed to avoid error and ambiguous.

The following sample case file is provided for particular scenarios and can act as your starting point to set up your own experimental configuration. Only mandatory variables are included initially. Settings not expressed in this case file can be added (see list of available settings “structures” section and Appendix). Validation will occur on all settings in your case file during the first “configuration” step. Settings/variables not expressed in case file will end up with their default values (established by the developers of the particular system). Several other pre-built case files are also included in the repository for reference purpose.

Case file example: [tutorial_case.yaml]

case:
  fv3_settings:
	CASE: C192
	LEVS: 65

  places:
	workflow_file: workflow/cycled_gfs.yaml

  settings:
	SDATE: 2016-02-10t00:00:00
	EDATE: 2016-02-12t00:00:00

	DUMP_SUFFIX: "p"
	run_gsi: No
	chgres_and_convert_ics: No
	gfs_cyc: 4 # run gfs every cycle



Detailed explanation of these files can be found in the “Structure / User Input Files” section.

The full configuration set are stored in a series of definition files written in YAML, a data serialization language in ASCII format (to be discussed later). Most of them are for background definition settings (Background Files there-after) which reflect the structures and features of a given modeling system (e.g. Global Workflow, Regional Workflow, HMON, etc.). Most configuration parameters come with default values which are also stored in these directories. These files are not designed to be edited by general users. However, when substantial upgrade of the modeling system happens where workflow-level modification is needed, these files need to be upgraded correspondingly, with collaboration between workflow and modeling teams.

Detailed explanation of these definition files will be given in the “Structure / Background Files” section. 
2. Configuration stage
Run experiment setup script

The setup_case.sh script is the entry point of the configuration step. It does the following:

Validate platform
Ingests user and case files along with all background files
Runs validation on inputted information - will exit here with validation errors and description
Builds experiment directory (including configs)
Builds COM directory

When setting up an experiment, the user needs to specify at least two required arguments to the setup_case.sh script: (1) case name (or full path to case file), and (2) experiment name (defined by the user). A third input is required if running on a HPC with multiple platforms (see -p flag in option flags information below).

	> setup_case.sh [options] $CASE_FILE  $EXPERIMENT_NAME

Examples: 	

> setup_case.sh tutorial_case test

OR

	> setup_case.sh ../cases/tutorial_case.yaml test

Note: the user can include the “.yaml” part of the case file name but it is not required unless providing the full path to the file

Option flags:

 - -p $HPC specify platform name $HPC, required if multiple platforms available (WCOSS options: WCOSS_C, WCOSS_DELL_P3)
 - -c skip COM directory creation (recommend to use when making your own initial conditions)
 - -f force COM directory re-creation and overwrite experimental directory files (does NOT overwrite platform.yaml)
 - -F force COM directory re-creation and overwrite experimental directory files (overwrite platform.yaml)
 - -v verbose mode
 - -d debug mode
 - -D super debug mode
 - -v -d -D, more and more screen output during workflow generation. -D will slow down the process quite significantly. Only recommended for developers.
 - -s sandbox mode. 

Enables workflow generation without supercomputer access. This option is developed for pure debugging purpose for CROW and workflow developers. When activated, CROW will skip platform validation. Ptmp, stmp and expdir will all defined under EXPROOT. User need to make sure writing access is granted for EXPROOT. 

	Example:	> setup_case.sh -fc -p WCOSS_DELL_P3 tutorial_case test

3. Generation stage
-------------------

Run workflow generation script

There are two equivalent scripts for setting up the experiment’s workflow (equivalent of setup_workflow.sh in the legacy configuration system): make_rocoto_xml_for.sh and make_ecflow_files_for.sh. The usage of them is almost identical with the setup_workflow.sh script of the legacy configuration system.

These two scripts are the entry points of the second step of creating a workflow, named Generation. They are shell scripts designed to set up the python environment and initiate the python functions inside “worktools.py”.
The $EXPERIMENT_DIRECTORY variable below is the location of your experiment files (e.g. configs). This is also known as $EXPDIR in some models.

Build Rocoto workflow

> make_rocoto_xml_for.sh  $EXPERIMENT_DIRECTORY

This will write a Rocoto xml file and a crontab file for recurring job. The usage and outcome is almost identical with the “setup_workflow.py” script of the legacy configuration system. However, instead of reading the config files, this file gets the configuration information totally by reading YAML configuration files under $EXPERIMENT_DIRECTORY. So, modifying the config files in the experiment directory won’t affect the outcome. Experiment directory config files are used by workflow jobs at run-time.

Rocoto is designed to be a self-contained and localized system that runs entirely in user space. It is easy for end-users to install, and run without help from systems administrators.

Detailed Rocoto documentation:

https://github.com/christopherwharrop/rocoto

Build ecFlow workflow

	> make_ecflow_files_for.sh  $EXPERIMENT_DIRECTORY

Note: When running with ecFlow,  the four “ECF” environment variables ($ECF_HOME, $ECF_ROOT, $ECF_PORT and $ECF_HOST) need to be properly set in your environment. (More details see ecFlow Training)

The major difference between ecFlow and Rocoto is that, ecFlow is a centralized workflow manager, which means it is usually installed in a designated place to serve all users of the system. The additional benefits of using ecFlow include a built-in graphic user interface, capability to handle dependencies on clock time, and elimination of crontab jobs. Furthermore, since NOAA/NCO has been using ecFlow as the workflow manager of operational workflows for years, using ecFlow will make it considerably easier for R2O transition compared with Rocoto.

ecFlow is a free software developed by ECMWF and licenced under Apache License 2.0. Currently EcFlow is built for all partitions of NOAA/WCOSS; Setting up ecFlow service for RDHPCS is still under going.

	Detailed ecFlow documentation: 

https://confluence.ecmwf.int/display/ECFLOW
