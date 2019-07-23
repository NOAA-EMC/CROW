Transition
=========================

This section is designed for users who are experienced users of the legacy configuration system. For these users, they may feel writing by their left hand for several days but it will get better soon.

Go-over the quick end-to-end with the tutorial case, make sure you understand the role of each step.
Create a simple rocoto xml with legacy configuration system, put it side-by-side with the one generated from CROW based system’s quick end-to-end.
Search for variables that makes the two XMLs different, then add them into proper section of your case file according to variable lists in Appendix b.
Rerun CROW script step 1 and 2 (setup_case; make_rocoto) several times, until rocoto xmls and the config files from legacy and CROW based configuration system match each other. 
Generate a benchmark case (typically located under /case/ and named ***_baseline.yaml), which includes all core jobs and features typical complexities of settings as the operational workflow, using CROW configuration system. And run it on operational platform (WCOSS)
Workout customized workflow from modifying the variables in the benchmark case.

These steps will help users to get used to the new configuration system in a gradual approach.

Future Plans
============================

Develop a case generator toolbox with GUI for easier generation of a case file.
Provide “group-level” default for all groups of the case file.
Include a set of “stub” J-JOBs to enable workflow level regression test without actually running the jobs. 
Develop “non-stop” option which user could generate workflow directly.
Appendix
Variable List

User Definition [user.yaml]

User_places [ PROJECT_DIR, HOMEgfs, HOMEcrow, NWPROD, DMPDIR, RTMFIX, EXPDIR, ROTDIR, ICSDIR, COMROOT, SHORT_TERM_TEMP, LONG_TERM_TEMP, HOMEDIR, NOSCRUB, FIXgsi, HOMEfv3gfs, HOMEpost, HOMEobsproc_prep, HOMEobsproc_network, BASE_VERIF, BASE_SVN, BASE_GIT, ics_from, parexp, HPSS_PAR_PATH]

accounting [ cpu_project, hpss_project, noscrub_project, ecflow_machine, ecflow_header, shared_partition, exclusive_partition, service_partition ]

Experiment [case.yaml]

settings, [dev_safeguards(True), realtime(False), run_vrfy_jobs(True), four_cycle_mode(False), rocoto_cycle_throttle(2), rocoto_task_throttle(5), use_nco_ecflow_headers(=four_cycle_mode), prod_util_module, ecflow_module, ecflow_real_clock, ecflow_virtual_clock, ecflow_hybrid_clock, ecflow_totality_limit, run_gsi, run_enkf, chgres_and_convert_ics, max_job_tries, IC_CDUMP, gfs_cyc, SDATE, EDATE, ics_from]

fv3_settings/fv3_gfs_settings/fv3_enkf_settings/fv3_gdas_settings [imp_physics, new_o3force, h2o_phys, do_vort_damp, consv_te, fv_sg_adj, dspheat, shal_cnv, agrid_vel_rst, cal_pre, do_sat_adjust, random_clds, cnvcld, dnats, IEMS, IALB, ISOL, IAER, ICO2, warm_start, read_increment, restart_interval, LEVS, FHCYC, FHCYC_GDAS, FHCYC_GFS, QUILTING, WRITE_NEMSIOFILE, WRITE_NEMSIOFLIP, nst_anl, lprecip_accu, DONST, MONO, MEMBER, d4_bg, dddmp, ISEED, SET_STP_SEED, DO_SHUM, DO_SKEB, DO_SPPT, RUN_EFCSGRP, ncld, nwat, zhao_mic, nh_type, USE_COUPLER_RES, cdmbgwd, CDUMP, CASE]

schedvar [cpu_project, shared_queue, service_queue, exclusive_queue, partition, shared_partition, service_partition, exclusive_partition, script_home, obsproc_network_home, obsproc_prep_home]

gfs_output_settings [FHOUT_GFS, FHMIN_GFS, FHMIN_ENKF, FHMAX_ENKF, FHOUT_ENKF, FHMIN_GDAS, FHMAX_GDAS, FHOUT_GDAS, FHMAX_HF_GFS, FHOUT_HF_GFS, NCO_NAMING_CONV, OUTPUT_FILE_TYPE, gfs_forecast_hours, gdas_forecast_hours, enkf_epos_fhr, wafs_last_hour, awips_g2_hours, awips_20km_1p0_hours]

data_assimilation [DOHYBVAR, NMEM_ENKF, NMEM_EOMGGRP, NMEM_EFCSGRP, NMEM_EARCGRP, RECENTER_ENKF, SMOOTH_ENKF, assim_freq, l4densvar, lwrite4danl, NSPLIT, NAM_ENKF, INCREMENTS_TO_ZERO, PREP_REALTIME, DO_EMCSFC, PROCESS_TROPCY, DO_RELOCATE, DO_MAKEPREPBUFR, OPREFIX, COM_OBS, COMIN_OBS, RERUN_EFCSGRP, RERUN_EOMGGRP, GENDIAG, NEPOSGRP, OBSINPUT_INVOBS, OBSQC_INVOBS, ENKF_INNOVATE_GROUPS, ENKF_FORECAST_GROUPS, ENKF_ARCHIVE_GROUPS]

post [GOESF, GTGF, FLXF, PGB1F, GFS_DOWNSTREAM, downset, NPOSTGRP, master_grid]

downstream [VDUMP, CDUMPFCST, CDFNL, MKPGB4PRCP, VRFYFITS, VSDB_STEP1, VSDB_STEP2, VRFYG2OBS, VRFYPRCP, VRFYRAD, VRFYOZN, VRFYMINMON, VRFYTRAK, VRFYGENESIS, RUNMOS, DO_POST_PROCESSING, DO_BUFRSND, DO_GEMPAK, DO_AWIPS, DO_FAX, DO_WAFS, DO_BULLETINS, FHOUT_CYCLONE_GFS, FHOUT_CYCLONE_GDAS]

places, same as user_places.

nsst, [ NST_MODEL, NST_RESV, ZSEA1, ZSEA2, NST_GSI, NSTINFO, NST_SPINUP]

archiving [ archive_to_hpss, arch_cyc, arch_warmicfreq, arch_fcsticfreq, copy_fit2obs_files, scrub_in_archive, scrub_in_archive_start, scrub_in_archive_end, ATARDIR ]

FAQ
=============================

Q: Which part of my work will be affected by starting to use CROW?
A: Only those before a Rocoto xml is generated.


Q: Do I need to be an expert of Python or YAML?
A: No. general users may not need to know python programming at all.


Q: Do I have to run CROW on a supercomputer?
A: CROW itself doesn’t require a supercomputer. However, The global-workflow does require a supercomputer to run. 

Q: What happens when there are multiple partitions available on a supercomputer?
A: You will have to specify the one you want by invoking the -p [platform] option, or it will stop.


Q: Can I manually edit configs in the experiment directory between the two steps?
A: No. You will need to edit the case file and start over from the first step. It will re-create the experiment directory while not affecting the experiment case that is currently running.

Q: Why not to overwrite platform file by default when user calls -f during setup_case?
A: The platform file is validated differently from other configuration files. Usually selection of long-term and short-term storage places is decided in this step by functions like “mmlsquota”, which returns the most empty partitions from a list of places (ie, /ptmp1, /ptmp2..). If the experiment case is already running, then overwriting the platform file could result in a different partition to be set as long-term or short-term storage other than the existing one. Obviously this is not anticipated. So a “-F” option was designed especially for those who want to overwrite the platform file.



Q: Why put all configs in the experiment directory at all if users are not recommended to edit them?
A: They mainly serve as “checkpoints” and documentation for your experiment settings. Along with the need to make the transition easier for users of legacy configuration system. A “non-stop” option will be included in the future releases within which user will be able to generate the desired workflow in only one step.

Q: Will CROW increase the runtime overhead of my workflow?
A: No. CROW doesn’t Once the workflow has been generated, it will run the same way as was generated in any other methods.

Q: Why reading all YAML at once every time even if I am doing really tiny changes?
A: Consistency. In a system as large and complex as the Global Workflow, inconsistency of cross-job arguments such as accounts, time or dependencies could take significant number of working hours from both human and supercomputers to fix. Among them, inconsistency results from accidental error of manual editing plays a big part. In other words, your “tiny” changes may affect the entire workflow, and our design helps make sure it is done correctly. For this reason, “patch editing” is neither implemented nor recommended.


Common Errors
======================================

Missing/conflicting python in environment

Message:
[Joe.Schmo@tfe07]$ ./setup_case.sh tutorial_case test
Lmod has detected the following error:  Cannot load module "intelpython/3.6.1.0" because these module(s) are loaded:
   Python
While processing the following module(s):
    Module fullname      Module Filename
    ---------------      ---------------
    intelpython/3.6.1.0  /apps/modules/modulefiles/intelpython/3.6.1.0
Cause:    A conflicting python module is loaded. May also get python error if you are missing python in your environment (module or PATH).
Fix:    Unload conflicting python module and/or load a python module or add python to your PATH

    [Joe.Schmo@tfe07 ecfutils]$ module unload python
Missing CROW submodule

Message:
[Joe.Schmo@tfe07 ecfutils]$ ./setup_case.sh tutorial_case test
Traceback (most recent call last):
  File "<string>", line 3, in <module>
  File "/scratch4/NCEPDEV/global/save/Joe.Schmo/git/global-workflow/workflow/worktools.py", line 34, in <module>
    import crow.tools, crow.config
ModuleNotFoundError: No module named 'crow'
Cause: forgot to checkout CROW sub-module
Cause:     You forgot to obtain the CROW submodule in your clone by running ‘git submodule’.
Fix:    Run submodule command at the top of global-workflow clone

    > git submodule update --init -recursive
Missing user file

Message:
[Joe.Schmo@tfe07 ecfutils]$ ./setup_case.sh tutorial_case test
ERROR:crow.model.fv3gfs:You did not create user.yaml!
ERROR:crow.model.fv3gfs:Copy user.yaml.default to user.yaml and edit.
Cause:     You forgot to create your user.yaml file, silly goose!
Fix:     Create your user.yaml. Under /workflow copy user.yaml.default to user.yaml and modify as needed to fit your account.
Experiment directory already exists

Message:
[Joe.Schmo@tfe07 ecfutils]$ ./setup_case.sh tutorial_case test
WARNING:crow.model.fv3gfs:/scratch4/NCEPDEV/global/noscrub/Joe.Schmo/expdir/test: already exists!
ERROR:crow.model.fv3gfs:Target directories already exist.
ERROR:crow.model.fv3gfs:I will not start a workflow unless you do -f.
CRITICAL:crow.model.fv3gfs:Use -f to force this workflow to start, but we aware that config, initial COM, and yaml files will be overwritten.  Other files will remain unmodified.
Cause:    Your experiment directory already exists so the script does not want to delete and remake it without warning you.
Fix:    Either remove the directory or use the ‘-f’ or ‘-F’ flags when running setup_case.sh to override the warning message and proceed with remaking experiment directory.
COM directory already exists

Message:
SURGE-slogin1 > ./setup_case.sh tutorial_case test
WARNING:crow.model.fv3gfs:/gpfs/hps3/ptmp/Joe.Schmo/comrot/test: already exists!
ERROR:crow.model.fv3gfs:Target directories already exist.
ERROR:crow.model.fv3gfs:I will not start a workflow unless you do -f.
CRITICAL:crow.model.fv3gfs:Use -f to force this workflow to start, but we aware that config, initial COM, and yaml files will be overwritten.  Other files will remain unmodified.
Cause:    Your COM directory already exists so the script does not want to delete and remake it without warning you.
Fix:    Either remove the directory or use the ‘-f’ flag when running setup_case.sh to override the warning message and proceed with remaking comrot.
Warning about missing initial condition files

Message:
Copy input conditions from: /gpfs/hps3/emc/global/noscrub/emc.glopara/ICS
Copy input conditions to: /gpfs/hps3/ptmp/Joe.Schmo/comrot/test
WARNING:crow.model.fv3gfs:/gpfs/hps3/emc/global/noscrub/emc.glopara/ICS/2018060400/C384/mem001/INPUT: link target does not exist
…
WARNING:crow.model.fv3gfs:/gpfs/hps3/emc/global/noscrub/emc.glopara/ICS/2018060400/C384/mem080/INPUT: link target does not exist
WARNING:crow.model.fv3gfs:/gpfs/hps3/emc/global/noscrub/emc.glopara/ICS/2018060400/gdas/C768/INPUT: link target does not exist
WARNING:crow.model.fv3gfs:/gpfs/hps3/emc/global/noscrub/emc.glopara/ICS/2018060400/gdas.t00z.abias: link target does not exist
WARNING:crow.model.fv3gfs:/gpfs/hps3/emc/global/noscrub/emc.glopara/ICS/2018060400/gdas.t00z.abias_pc: link target does not exist
WARNING:crow.model.fv3gfs:/gpfs/hps3/emc/global/noscrub/emc.glopara/ICS/2018060400/gdas.t00z.abias_air: link target does not exist
WARNING:crow.model.fv3gfs:/gpfs/hps3/emc/global/noscrub/emc.glopara/ICS/2018060400/gdas.t00z.radstat: link target does not exist
Cause:    The script expects to find the ICs on disk to link to but they are missing.
Fix:    a) Can ignore if you plan to move your own ICs into your COM directory or b) can rerun setup_case.sh with ‘-c’ flag to not create COM directory or attempt to make links or c) if ICs should be there resolve missing files and rerun script
Missing PROJECT_DIR setting in user file

Message:
SURGE-slogin1 > ./setup_case.sh -f tutorial_case test
Traceback (most recent call last):
  File "/scratch4/NCEPDEV/global/save/Joe.Schmo/global-workflow/workflow/CROW/crow/config/eval_tools.py", line 106, in from_config
    result=val._result(globals,locals)
  File "/scratch4/NCEPDEV/global/save/Joe.Schmo/global-workflow/workflow/CROW/crow/config/eval_tools.py", line 49, in _result
    raise ConfigUserError(eval("f'''"+self+"'''",c,locals))
crow.config.exceptions.ConfigUserError: Please select a project directory.
Cause:    You forgot to set PROJECT_DIR in your user.yaml.
Fix:    Set PROJECT_DIR in your user.yaml and try again.
 
