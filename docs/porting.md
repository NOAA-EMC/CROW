Porting to a new platform
===========================

The availability and easiness of porting the entire workflow across various computing platform is one of the design principles of CROW at the start. When using CROW, all platform-specific settings should be specified in one of the platform.yaml files located under workflow/platform.

It is worth to be mentioned that porting workflow to a new(target) platform is not a trivial job given the distinct supercomputing environment from one to another regarding both hardware and software system. Also, all elements and subsystems need to be fully tested on the target platform before the system-wide porting efforts. Successful and efficient porting of workflow could be carried out only through collaborative efforts between the workflow team and modeling team.

Following is the common procedure to transfer a CROW driven workflow system to another machine:
Make sure all libraries and modules required for the workflow system are in place on the target machine, including Python 3.6+ and PyYAML library of Python.
Make sure all elements of the chosen workflow (code, build system, scripts) work for the target machine. 
Run CROW unit test.
Compose all required YAMLs for that platform.
Set up a benchmark case for that platform. The benchmark case should be both reflecting the normal real-world complexity and workload, and able to be validated.
