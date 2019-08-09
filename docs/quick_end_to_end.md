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
Copy default user file to your user file:

	> cp user.yaml.default user.yaml
Open and modify user.yaml, the following are required to be set:

	- PROJECT_DIR: Place for experiment directory, make sure you have write access.
	- cpu_project: cpu project that you are working with.
	- hpss_project: hpss project that you are working with.

Run experiment setup script

	> cd CROW
	> ./setup_case.sh tutorial_free_forecast test
	
If you see the following error:

	ERROR:crow.model.fv3gfs:More than one platform is available: $PLAT1, $PLAT2
	ERROR:crow.model.fv3gfs:Pick one with -p option

That means you could access more than one computing platform from this environment (which is good). You need to make selection of computing platform between $PLAT1 and $PLAT2 by do the following:

In CROW, there's a '-p' command option to the setup_case command:

	> ./setup_case.sh -p $PLAT_x tutorial_free_forecast test
	
Execute this instead of the standard one, while $PLAT_x is the platform that you want to select.

Run workflow generation script

	> ./make_rocoto_xml_for.sh $EXPERIMENT_DIRECTORY

...where $EXPERIMENT_DIRECTORY is the location of the folder created in the prior step (which contains your generated config files); this is where your resulting xml file will be found

Navigate to your experiment directory and start your experiment with Rocoto:

> module load rocoto
> rocotorun -d workflow.db -w workflow.xml
