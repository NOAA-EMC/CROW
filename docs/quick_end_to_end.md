Quick End-to-end
==================

How to setup a stock experiment with Rocoto:

Checkout repository “CROWdemo2” branch

> git clone gerrit:global-workflow
> cd global-workflow
> git checkout CROWdemo2

Get CROW submodule

> git submodule update --init --recursive

Build/link global-workflow

	> cd sorc
	> sh checkout.sh
	> sh build_all.sh
	> sh link_fv3gfs.sh emc $target
	...where $target is machine (wcoss_cray, theia, jet, or dell)

Set up user file

While at the top of global-workflow clone:
> cd workflow
Copy default user file to your user file
	> cp user.yaml.default user.yaml
Open and modify user.yaml, the following are required to be set:
	EXPROOT, cpu_project and hpss_project

Run experiment setup script

	> cd CROW
> ./setup_case.sh tutorial_free_forecast test

Run workflow generation script

	> ./make_rocoto_xml_for.sh $EXPERIMENT_DIRECTORY

...where $EXPERIMENT_DIRECTORY is the location of the folder created in the prior step (which contains your generated config files); this is where your resulting xml file will be found

Navigate to your experiment directory and start your experiment with Rocoto:

> module load rocoto
> rocotorun -d workflow.db -w workflow.xml
