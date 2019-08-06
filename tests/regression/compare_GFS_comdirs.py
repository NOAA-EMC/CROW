#!/usr/bin/env  python3

import filecmp
import collections
import os,sys
from pathlib import Path
from pathlib import PurePath

egnore_file_list = ['.git','*.grp*','*.log','*.log*','INPUT','logs','*.idx']

def get_args():
    import argparse
    import json
    global using_file_list
    global file_dic_list

    parser = argparse.ArgumentParser()
    #group  = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('--cmp_dirs',nargs=2,metavar=('ROTDIR_baseline','ROTDIR_testrun'),help='compare ROTDIR folders')
    parser.add_argument('-ujf','--cmp_dirs_with_joblevel_file', nargs=1, metavar=('file_list.yaml'), help='(u)se stored (j)ob level (f)ile list when comparing ROTDIRS')
    parser.add_argument('-cjf','--creat_jobslevel_file',nargs=3,metavar=('job_name','ROTDIR','file_list.yaml'),help='(c)reate (j)ob level (f)ile from output')
    parser.add_argument('-f','--diff_list_file',dest="diff_list_file",help='name of file containing a list of differing files')
    parser.add_argument('-vt','--verbose_tar', help='include names of differing files witin tar files', action='store_true',default=False)

    args = parser.parse_args()
    if args.cmp_dirs is not None:
        for dirs in args.cmp_dirs:
            if not Path(dirs).is_dir():
                logger.critical('directory %s does not exsist'%dirs)
                sys.exit(-1)

    using_file_list = False
    if args.cmp_dirs_with_joblevel_file is not None:
        if Path(args.cmp_dirs_with_joblevel_file[0]).is_file():
            yaml_file_open =  open(args.cmp_dirs_with_joblevel_file[0], 'r')
            try:
                file_dic_list = yaml.load( yaml_file_open, Loader=yaml.Loader )
                using_file_list = True
            except yaml.YAMLError as exc:
                logger.critical(logger_hdr+'argument %s is not a valid YAML file')
        else:
            logger.critical(logger_hdr+'argument %s is not a valid YAML file')

    return args


def compare(folder1, folder2 ):
    return _recursive_dircmp(folder1, folder2)

def _recursive_dircmp(folder1, folder2 ):

    comparison = filecmp.dircmp(folder1, folder2,  ignore=egnore_file_list)
    data = {
        'left': [r'{}/{}'.format(folder1, i) for i in comparison.left_only],
        'right': [r'{}/{}'.format(folder2, i) for i in comparison.right_only],
        'both': [r'{}/{}'.format(folder1, i) for i in comparison.common_files]
    }

    for datalist in data.values():
        datalist.sort()

    if comparison.common_dirs:
        for folder in comparison.common_dirs:
            sub_folder1 = os.path.join(folder1, folder)
            sub_folder2 = os.path.join(folder2, folder)
            sub_report = _recursive_dircmp(sub_folder1, sub_folder2)

            for key, value in sub_report.items():
                data[key] += value

    return data

def tarcmp(tar_file_one, tar_file_two):

    import hashlib
    import tarfile
    import zipfile

    tar1_path = os.path.dirname( tar_file_one )
    tar2_path = os.path.dirname( tar_file_two )

    tar1 = tarfile.open( tar_file_one, mode="r" )
    tar2 = tarfile.open( tar_file_two, mode="r" )

    chunk_size = 100*1024
    diff_members = []

    for member1,member2 in list(zip(tar1, tar2)):

        if not member1.isfile():
            continue

        if member1.name[-4:] == '.zip':
            diff_zip_members = zipcmp( member1, member2 )
            if not verbose and len(diff_zip_members) != 0:
                return False
            diff_members += diff_zip_members
            continue

        if member1.name[-3:] == '.gz':
            #print( 'located gzip file %s'%member1.name)
            if not gzcmp(tar1, tar2, member1, member2 ):
                if not verbose:
                    return False
                diff_members.append( member1.name )
            continue

        store_digests = {}

        f1 = tar1.extractfile(member1)
        h1 = hashlib.new('md5')
        data1 = f1.read(chunk_size)

        f2 = tar2.extractfile(member2)
        h2 = hashlib.new('md5')
        data2 = f2.read(chunk_size)

        while data1:
            h1.update(data1)
            data1 = f1.read(chunk_size)
        while data2:
            h2.update(data2)
            data2 = f2.read(chunk_size)

        if h1.hexdigest() != h2.hexdigest():
            if verbose:
                diff_members.append(member1.name)
            else:
                return False
    if verbose:
        return diff_members
    else:
        return True

def cmp_master_grb2(grib2_file1, grib2_file2):
    l1 = l2 = ' '
    with open(grib2_file1, 'r',encoding="ISO-8859-1") as f1, open(grib2_file2, 'r',encoding="ISO-8859-1") as f2:
        firstline1 = f1.readline(); firstline2 = f2.readline()
        if '!GFHDR!' in firstline1:
            f1.readline(); f2.readline()
        while l1 != '' and l2 != '':
            if l1 != l2:
                return False
            l1 = f1.readline()
            l2 = f2.readline()
    return True


def gzcmp(tar1, tar2, member1, member2):

    import hashlib
    import gzip
    import tarfile
    import tempfile

    tmpdirname_gzip1 = tempfile.mkdtemp()
    tmpdirname_gzip2 = tempfile.mkdtemp()
    tar1.extract( member1, path=tmpdirname_gzip1)
    tar2.extract( member2, path=tmpdirname_gzip2)

    extracted_file1_name =  os.path.join( tmpdirname_gzip1, member1.name ) 
    extracted_file2_name =  os.path.join( tmpdirname_gzip2, member2.name )

    #print( 'extracted file1 %s'%extracted_file1_name)
    #print( 'extracted file2 %s'%extracted_file2_name)

    chunk_size = 100*1024
    gzip_file1 = gzip.open( extracted_file1_name )
    gzip_file2 = gzip.open( extracted_file2_name )

    h1 = hashlib.new('md5')
    data1 = gzip_file1.read(chunk_size)
    h2 = hashlib.new('md5')
    data2 = gzip_file2.read(chunk_size)

    while data1:
        h1.update(data1)
        data1 =  gzip_file1.read(chunk_size)
    while data2:
        h2.update(data2)
        data2 =  gzip_file2.read(chunk_size)

    #print( 'h1',  h1.hexdigest() )
    #print( 'h2',  h2.hexdigest() )
    if h1.hexdigest() == h2.hexdigest():
        return True
    else:
        return False

def zipcmp(member1, member2):

    import hashlib
    import zipfile
    import tarfile
    import tempfile

    tmpdirname_zip1 = tempfile.mkdtemp()
    tmpdirname_zip2 = tempfile.mkdtemp()

    tarfile.extract( member1, path=tmpdirname_zip1)
    tarfile.extract( member2, path=tmpdirname_zip2)

    zip_file_one = os.path.join( tmpdirname_zip1, member1.name )
    zip_file_two = os.path.join( tmpdirname_zip2, member2.name )

    diff_zip_members = []

    break_return = False
    if not zipfile.is_zipfile(zip_file_one):
        logger.warning(logger_hdr+'file %s has a zip extension but is not a zip file'%zip_file_one)
        break_return = True
    if not zipfile.is_zipfile(zip_file_two):
        logger.warning(logger_hdr+'file %s has a zip extension but is not a zip file'%zip_file_two)
        break_return = True
    if break_return:
        return diff_zip_members

    zip1 = zipfile.ZipFile( zip_file_one, mode="r" )
    zip2 = zipfile.ZipFile( zip_file_two, mode="r" )

    chunk_size = 100*1024

    logger.info(logger_hdr+'checking zipfiles %s and %s'%(member1.name,member2.name))
    for member_zip1,member_zip2 in list(zip(zip1.namelist(), zip2.namelist())):
        if not member_zip1.isfile():
            continue

        store_digests = {}

        z1 = zip1.extract( member_zip1,tmpdirname_zip1 )
        z1_extractedfile_fp = open( z1.name )
        h1 = hashlib.new('md5')
        data1 = z1_extractedfile_fp.read(chunk_size)

        z2 = zip2.extractfile(member_zip2,tmpdirname_zip2 )
        z2_extractedfile_fp = open( z2.name )
        h2 = hashlib.new('md5')
        data2 = z2_extractedfile_fp.read(chunk_size)

        while data1:
            h1.update(data1)
            data1 =  z1_extractedfile_fp.read(chunk_size)
        while data2:
            h2.update(data2)
            data2 =  z1_extractedfile_fp.read(chunk_size)

        if h1.hexdigest() != h2.hexdigest():
            diff_zip_members.append( z1.name + ' in zip file %s'%member1.name )
           
    return diff_zip_members

def tarcmp_verbose(tar_file_one, tar_file_two):

    import hashlib
    import tarfile

    comp_tars = []
    files_md5 = {}
    comp_tars.append( tar_file_one )
    comp_tars.append( tar_file_two )
    diff_members = []

    for tar_file in comp_tars:

        tar = tarfile.open( tar_file, mode="r" )

        chunk_size = 100*1024
        store_digests = {}
        files_md5[tar_file] = {}

        for member in tar:
            if not member.isfile():
                continue
            f = tar.extractfile(member)
            h = hashlib.new('md5')
            data = f.read(chunk_size)
            while data:
                h.update(data)
                data = f.read(chunk_size)
            files_md5[tar_file][member.name] = h.hexdigest()

    if len(files_md5[tar_file_one]) != len(files_md5[tar_file_two]):
        return diff_members

    for member in files_md5[tar_file_one]:
        if files_md5[tar_file_one][member] != files_md5[tar_file_two][member]:
            diff_members.append(member)
    return diff_members


def netcdfver(filename):
#    Returns one of three strings based on the NetCDF version of the
#    given file, or returns None if the file is not NetCDF:
#     *  "CDF1" = NetCDF classic format
#     *  "CDF2" = NetCDF 64-bit offset format
#     *  "HDF5" = HDF5 file, and hence possibly a NetCDF4 file.
#     *  None   = Not NetCDF and not HDF5
    import codecs
    with open(filename,'rb') as f:
        eight=f.read(8)
        if len(eight)<4:
            return None
        four=eight[0:4]
        if four==b'CDF\x01':
            return "CDF1"
        elif four==b'CDF\x02':
            return "CDF2"
        elif eight==b'\x89\x48\x44\x46\x0d\x0a\x1a\x0a':
            return "HDF5"
    return None

def print_diff_files(dcmp):

    import tarfile
    import subprocess
    from subprocess import run

    global diff_file; global cwd; global verbose; global zero_sized_files_list
    global fixed_dir_experment_name
    if len(dcmp.common_dirs) != 0 and not verbose:
        logger.info(logger_hdr+'checking directories: %s'%' '.join(dcmp.common_dirs))
    if len( dcmp.diff_files ) == 0 and len(dcmp.common_files) != 0:
        logger.info(logger_hdr+'out of %d common files no differences found'%len(dcmp.common_files))
    file1_shortpath = '/'+dcmp.left.replace(cwd,'').replace(fixed_dir_experment_name,'').lstrip('/')
    logger.info(logger_hdr+'checked in directory %s'%(file1_shortpath))
    if len( dcmp.diff_files) != 0 and verbose:
        number_netcdf_files = len([s for s in dcmp.diff_files if '.nc' in s])
        logger.info(logger_hdr+'checking %d differing files of which %d are NetCDF and some may be tar files'%(len(dcmp.diff_files),number_netcdf_files))
    num_netcdf_differing_files = 0
    num_netcdf_differing_files_onlyheader = 0
    num_tar_differing_files = 0
    num_identified_tar_files = 0
    num_differing_files = 0
    for name in dcmp.diff_files:

        #file_from_jobs = []
        #if using_file_list:
        #    logger.info(logger_hdr+'looking to see if file %s is in yaml job list'%name)
        #    file_from_jobs = [ v for k,v in file_dic_list.items() if name in k]
        #if len(file_from_jobs) != 0:
        #    print( 'HERE IS ONE: ', file_from_jobs )
        #    sys.exit(0)
        #else:
        #    logger.info(logger_hdr+'file %s not in yaml file'%name)

        file1 = os.path.join(dcmp.left,name); file2 = os.path.join(dcmp.right,name)
        file1_shortpath = dcmp.left.replace(cwd,'').replace(fixed_dir_experment_name,'').lstrip('/')
        file2_shortpath = dcmp.right.replace(cwd,'').replace(fixed_dir_experment_name,'').lstrip('/')
        if '/' in file1_shortpath:
            file1_shortpath = '/'+file1_shortpath
        if '/' in file2_shortpath:
            file2_shortpath = '/'+file2_shortpath
        diff_tar_members = []
        if len(zero_sized_files_list) > 0:
            for zero_sized_file in zero_sized_files_list:
                diff_file.write('warning: this is a zero legth file: %s\n'%zero_sized_file)
        if 'master.grb2' in name:
            if not cmp_master_grb2( file1, file2 ):
                diff_file.write( 'grib2 file %s has data differences in directories %s and %s\n'%(name,file1_shortpath,file2_shortpath))
            else:
                logger.info(logger_hdr+'grib2 file %s only differed in the header'%name)
        elif '.nc' in name:
            net_cdf_type = netcdfver(file1)
            if net_cdf_type is not None:
                if verbose:
                    netcdf_diff_output = run([NCCMP, "--threads=4", "--data", file1, file2], stderr=subprocess.PIPE).stderr.decode('utf-8').strip()
                else:
                    netcdf_diff_output = run([NCCMP, "--diff-count=3", "--threads=4", "--data", file1, file2], stderr=subprocess.PIPE).stderr.decode('utf-8').strip()
                if len(netcdf_diff_output) == 0:
                    diff_file.write('NetCDF file %s of type: %s differs only in the header in directories %s and %s\n'%(name,net_cdf_type,file1_shortpath,file2_shortpath))
                    num_netcdf_differing_files_onlyheader += 1
                else: 
                    diff_file.write( 'NetCDF file %s of type: %s differs %s in directories %s and %s\n'%(name,net_cdf_type,netcdf_diff_output,file1_shortpath,file2_shortpath))
                    num_netcdf_differing_files += 1
        elif tarfile.is_tarfile(file1):
            num_identified_tar_files += 1
            if verbose:
                diff_tar_members = tarcmp( file1, file2 )
                if len(diff_tar_members) != 0:
                    logger.info(logger_hdr+'%d memebers of tar file %s are differing'%(len(diff_tar_members),name))
                    for tar_file_member in diff_tar_members:
                        diff_file.write('tar member file %s differs in tar file %s from directories %s and %s\n' % (tar_file_member, name, file1_shortpath, file2_shortpath))
                else:
                    logger.info(logger_hdr+'all the memebers of tar file where identical')
            else:
                if not tarcmp( file1, file2 ):
                    diff_file.write('tar file %s differs in directories %s and %s\n' % (name, file1_shortpath, file2_shortpath))
                    num_tar_differing_files += 1
        else:
            diff_file.write('file %s differs in directories %s and %s\n'% (name, file1_shortpath, file2_shortpath))
            num_differing_files += 1
        diff_file.flush()
    if num_netcdf_differing_files != 0:
        logger.info(logger_hdr+'%d NetCDF files differed'%num_netcdf_differing_files)
    if num_tar_differing_files != 0:
        logger.info(logger_hdr+'%d tar files differed'%num_tar_differing_files)
        if verbose:
            if len(diff_tar_members) == 0:
                logger.info(logger_hdr+'of the %d tar files intentifed as differing had no members different'%num_tar_differing_files)
            else:
                logger.info(logger_hdr+'of the %d tar files intentifed as differing had $d members different'%(num_tar_differing_files,len(num_tar_differing_files)))
    if num_differing_files != 0:
        logger.info(logger_hdr+'%d files differed that was not NetCDF nor a tar files'%num_differing_files)

    for sub_dcmp in dcmp.subdirs.values():
        print_diff_files(sub_dcmp)

def capture_files_dir( input_dir ):

    current_file_list = []
    for path, subdirs, files in os.walk(input_dir,followlinks=True):
        for name in files:
            if '.log' not in name:
                current_file_list.append( os.path.join(path, name) )
    return current_file_list

def get_logger():
    import logging
    logger = logging.getLogger('python'); logger_hdr = 'LOG : '
    logger.setLevel(level=logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(level=logging.INFO)
    formatter = logging.Formatter('%(levelname)s : %(name)s : %(asctime)s : %(message)s','%Y-%m-%d %H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger,logger_hdr

if __name__ == '__main__':

    import datetime
    import time
    import yaml
    import subprocess
    from subprocess import run
    from os import environ

    logger,logger_hdr = get_logger()
    args = get_args()

    if 'REGRESSSION_ROTDIR_BASENAME' in os.environ:
        fixed_dir_experment_name = environ.get('REGRESSSION_ROTDIR_BASENAME')
    else:
        fixed_dir_experment_name = 'fv3gfs_regression_ROTDIRS'
    using_file_list = False

    NCCMP='/gpfs/hps3/emc/nems/noscrub/emc.nemspara/FV3GFS_V0_RELEASE/util/nccmp'
    NCCMP_path = Path(NCCMP)
    if not NCCMP_path.is_file():
        try:
            NCCMP=run(['which','nccmp'],stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
        except subprocess.CalledProcessError:
            logger.critical(logger_hdr+'nccmp tool not found')
            sys.exit(-1)
        if len(NCCMP)==0:
            logger.critical(logger_hdr+'nccmp tool not found')
            sys.exit(-1)

    try:
        nccmp_version = run([NCCMP, '--version'], stderr=subprocess.PIPE).stderr.decode('utf-8').strip()
        nccmp_version = nccmp_version.splitlines()[0]
    except subprocess.CalledProcessError as nccmp_err:
        logger.critical(logger_hdr+"nccmp tool found but failed exit code %s (try 'module load PrgEnv-intel')"%nccmp_err)
        sys.exit(-1)

    logger.info(logger_hdr+'using %s for comparing NetCDF files'%nccmp_version)

    process_time = time.process_time()

    verbose = args.verbose_tar
    file_dic_list = collections.defaultdict(list)
    zero_sized_files_list = list()

    if args.creat_jobslevel_file is not None:

        job_name = args.creat_jobslevel_file[0]
        ROTDIR = args.creat_jobslevel_file[1]
        ROTDIR_Path = Path( args.creat_jobslevel_file[1] )
        if not ROTDIR_Path.is_dir():
            logger.critical(logger_hdr+'ROTDIR %s is not a directory')
            sys.exit(-1)
        ROTDIR = os.path.realpath( ROTDIR ) 
        yaml_files_filename =  os.path.realpath( args.creat_jobslevel_file[2] )
        logger.info(logger_hdr+'determining job level files for job %s in file %s from ROTDIR %s'%(job_name, os.path.basename(yaml_files_filename),ROTDIR))
        file_list_current = capture_files_dir( ROTDIR )
        yaml_files_filename_Path = Path(yaml_files_filename)
        if yaml_files_filename_Path.is_file():
            yaml_files_fptr = open(  yaml_files_filename )
            file_dic_list = yaml.full_load( yaml_files_fptr  )
            yaml_files_fptr.close()

        if 'prior_ROTDIR' in file_dic_list:
            result = []
            logger.info(logger_hdr+'prior out from last job found %s'%yaml_files_filename )
            for file in file_list_current:
                if file not in file_dic_list['prior_ROTDIR']:
                    result.append(file)
            file_dic_list[job_name] = result
            logger.info(logger_hdr+'%d files added from job %s'%( len(file_dic_list[job_name]), job_name ))
        else:
            logger.info(logger_hdr+'no prior job found job, %d files added to list from job %s'%( len(file_list_current), job_name ) )
            file_dic_list[job_name] = file_list_current
            
        file_dic_list['prior_ROTDIR'] = file_list_current
        logger.info(logger_hdr+'write out file %s'%yaml_files_filename )
        with open(yaml_files_filename, 'w') as outfile:
            yaml.dump(file_dic_list, outfile, default_flow_style=False)

    if  args.cmp_dirs is None:
        logger.info( logger_hdr+'compare_folders script is being used to capture job level files only and is quitting')
        sys.exit(0)

    folder1 = os.path.realpath( args.cmp_dirs[0] )
    folder2 = os.path.realpath( args.cmp_dirs[1] )

    if args.diff_list_file:
        diff_file_name = args.diff_list_file
    else:
        now_date_time  = datetime.datetime.now().strftime('%d-%m-%Y-H%H')
        diff_file_name = 'diff_file_list_%s.lst'%now_date_time
    diff_file_number = 0
    while os.path.exists(diff_file_name):
        diff_file_number += 1
        diff_file_name_base = os.path.basename(diff_file_name)
        diff_file_name = os.path.join(os.path.dirname(diff_file_name),diff_file_name_base.rsplit('_',1)[0]+'_'+str(diff_file_number)+'.lst')

    for folder in (folder1,folder2):
        if not os.path.isdir(folder):
            logger.critical(logger_hdr+'directory %s does not exsist'%folder)
            sys.exit(-1)
    diff_file = open( diff_file_name,'w')

    cwd = os.getcwd()

    total_file_count_dir1 = sum([len(files) for r, d, files in os.walk(folder1)])
    total_file_count_dir2 = sum([len(files) for r, d, files in os.walk(folder2)])

    import pathlib
    logger.info(logger_hdr+'a safty sanity check for zero sized files is processing')
    for folder in (folder1,folder2):
        for path, subdirs, files in os.walk(folder):
            for name in files:
                if pathlib.Path(pathlib.PurePath(path,name)).exists():
                    file_name_found = pathlib.PurePath(path,name)
                    if os.path.getsize( file_name_found ) == 0:
                        if file_name_found.name.split('_')[-1] not in ('run','events'):
                            zero_sized_files_list.append(file_name_found)
                            logger.warning( "%s is a zero sized file "%file_name_found )

    logger.info(logger_hdr+'total number of files in %s is %d'%(folder1,total_file_count_dir1))
    logger.info(logger_hdr+'total number of files in %s is %d'%(folder2,total_file_count_dir2))
    logger.info(logger_hdr+'comparing folders:\n   %s\n   %s'%(folder1,folder2))

    results = compare(folder1, folder2)

    logger.info(logger_hdr+'checking for matching file counts in directories')
    left_right = ('left','right')
    out_of_order_file_name = os.path.join( os.path.dirname( diff_file_name ), os.path.basename(diff_file_name).split('.',1)[0]+'.file_imbalance')
    out_of_order_file = open(out_of_order_file_name ,'w')
    for each_side in left_right:
        if each_side == 'left':
            foldera = folder1
            folderb = folder2
        else:
            folderb = folder1
            foldera = folder2
        num_missmatched_files = len(results[each_side])
        if num_missmatched_files != 0:
            logger.info('%d files found in %s that are not in %s list written to %s'\
            %(num_missmatched_files,os.path.basename(foldera),os.path.basename(folderb), out_of_order_file_name))
            out_of_order_file.write('%d files found in %s that are not in %s:\n'%(num_missmatched_files,os.path.basename(foldera),os.path.basename(folderb)))
            for file in results[each_side]:
                out_of_order_file.write('   %s'%file+'\n')
            out_of_order_file.flush()
    logger.info(logger_hdr+'checking for file differences...')
    compare_files = filecmp.dircmp(folder1, folder2, ignore=egnore_file_list)
    print_diff_files( compare_files )
    elapsed_time = time.process_time() - process_time 
    logger.info(logger_hdr+'comparing fv3gfs output directories completed. Time to process(%.4f seconds)'%elapsed_time)
    diff_file.close()
