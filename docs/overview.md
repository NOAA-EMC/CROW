Overview
=======

The “Configurator for Research and Operational Workflow” (CROW) is a workflow toolbox that automates and streamlines the generation and configuration of EMC workflows, as well as connects system jobs (referred to as J-jobs in NCEP parlance) to a workflow manager like Rocoto or ecFlow.

![Figure 1. Structure of Global Workflow, downstream jobs not included](/image/img1.jpg)
 - The arrows in this chart indicates the flow of configuration information. 
 - Round-cornered boxes are ASCII files at various stages, while diamond-shapes are scripts run by the user. 
 - Yellow color indicates places for user input, while dark green boxes are the final products.

The increasing level of complexity of EMC workflows lead to several challenges for researchers and users. Most noticeably the difficulty for collaboration, documentation and R2O transition. Among them, one of the major issues is model configuration. In figure 1 below, we can see that the legacy way to configure the global workflow (e.g. for the FV3GFS) was through editing config files and manipulating the command line variables of setup_expt script. This approach was becoming increasingly time consuming, unmanageable and error-prone with the growing complexity of the system structure. 

![Figure 2. Legacy configuration system flowchart for users](/image/img2.jpg)

The arrows in this chart indicates the flow of configuration information. 
Round-cornered boxes are ASCII files at various stages, while diamond-shapes are scripts run by the user. 
Yellow color indicates places for user input, while dark green boxes are the final products.

The legacy method for establishing model experiments had little automation and relied on the user too heavily, leading to errors discovered after compute resources were already used and thus wasted. The effort taken to modernize the configuration system aimed to help standardize the process of setting up a workflow, minimize the efforts of researchers, and increase accountability.

A summary of the benefits of this smart, automated, flexible workflow toolbox are:

 - Easier addition or removal of system jobs
 - Easier collaboration
 - Easier R2O transition
 - Easier documentation of model configurations
 - Turn-key conversion between different workflow managers (e.g. Rocoto or ecFlow). 


~~~~~~~~~~~~~{.yaml}
user_places: &user_places
    PROJECT_DIR: !error Please select a project directory.
accounting: & accounting
    cpu_project: !error What accounting code do I use to submit jobs? # ie.: global
    hpss_project: !error Where do I put data on HPSS?   # ie.: emc-global
~~~~~~~~~~~~~

