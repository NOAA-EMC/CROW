#!/gpfs/hps3/emc/nems/noscrub/Samuel.Trahan/python/3.6.1-emc/bin/python3

import filecmp
import collections
import os,sys
from pathlib import Path

def compare(folder1, folder2 ):
    return _recursive_dircmp(folder1, folder2)

def _recursive_dircmp(folder1, folder2 ):

    comparison = filecmp.dircmp(folder1, folder2)
    data = {
        'left': [r'{}/{}'.format(folder1, i) for i in comparison.left_only],
        'right': [r'{}/{}'.format(folder2, i) for i in comparison.right_only],
        'both': [r'{}/{}'.format(folder1, i) for i in comparison.common_files],
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

    tar1 = tarfile.open( tar_file_one, mode="r" )
    tar2 = tarfile.open( tar_file_two, mode="r" )
    chunk_size = 100*1024

    for member1,member2 in list(zip(tar1, tar2)):
        if not member1.isfile():
            continue

        store_digests = {}

        f1 = tar1.extractfile(member1)
        h1 = hashlib.new('md5')
        data1 = f1.read(chunk_size)
        f2 = tar2.extractfile(member1)
        h2 = hashlib.new('md5')
        data2 = f2.read(chunk_size)

        while data1:
            h1.update(data1)
            data1 = f1.read(chunk_size)
        while data2:
            h2.update(data2)
            data2 = f2.read(chunk_size)

        if h1.hexdigest() != h2.hexdigest():
            return False

    return True

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

    NCCMP='/gpfs/hps3/emc/nems/noscrub/emc.nemspara/FV3GFS_V0_RELEASE/util/nccmp'
    NCCMP_path = Path(NCCMP)
    if not NCCMP_path.is_file():
        try:
            NCCMP=run(['which','nccmp'],stdout=subprocess.PIPE).stdout.decode('utf-8').strip()
        except subprocess.CalledProcessError:
            logger.critical(logger_hdr+'nccmp tool not found')
            sys.exit(1)
        if len(NCCMP)==0:
            logger.critical(logger_hdr+'nccmp tool not found')
            sys.exit(1)

    global diff_file; global cwd; global verbose
    global fixed_dir_experment_name
    for name in dcmp.diff_files:
        if '.log' in name:
            continue
        file1 = os.path.join(dcmp.left,name); file2 = os.path.join(dcmp.right,name)
        file1_shortpath = dcmp.left.replace(cwd,'').replace(fixed_dir_experment_name,'').lstrip('/')
        file2_shortpath = dcmp.right.replace(cwd,'').replace(fixed_dir_experment_name,'').lstrip('/')
        if '.nc' in name:
            net_cdf_type = netcdfver(file1)
            if net_cdf_type is not None:
                if verbose:
                    netcdf_diff_output = run([NCCMP, "--threads=4", "--data", file1, file2], stderr=subprocess.PIPE).stderr.decode('utf-8').strip()
                else:
                    netcdf_diff_output = run([NCCMP, "--diff-count=3", "--threads=4", "--data", file1, file2], stderr=subprocess.PIPE).stderr.decode('utf-8').strip()
                if len(netcdf_diff_output) == 0:
                    diff_file.write('NetCDF file %s of type: %s differs only in the header in directories %s and %s\n'%(name,net_cdf_type,file1_shortpath,file2_shortpath))
                else: 
                    diff_file.write( 'NetCDF file %s of type: %s differs %s in directories %s and %s\n'%(name,net_cdf_type,netcdf_diff_output,file1_shortpath,file2_shortpath))
        elif tarfile.is_tarfile(file1):
            if verbose:
                diff_tar_members = tarcmp_verbose( file1, file2 )
                if len(diff_tar_members) != 0:
                    for diff_file in diff_tar_members:
                        diff_file.write('tar member file %s differs in tar file %s from directories %s and %s\n' % (diff_file, name, file1_shortpath, file2_shortpath))
            if not tarcmp( file1, file2 ):
                diff_file.write('tar file %s differs in directories %s and %s\n' % (name, file1_shortpath, file2_shortpath))
        else:
            diff_file.write('file %s differs in directories %s and %s\n'% (name, file1_shortpath, file2_shortpath))
        diff_file.flush()

    for sub_dcmp in dcmp.subdirs.values():
            print_diff_files(sub_dcmp)

def capture_files_dir( input_dir ):

    #current_file_list = collections.defaultdict(list)
    current_file_list = []
    for path, subdirs, files in os.walk(input_dir):
        for name in files:
            current_file_list.append( os.path.join(path, name) )
    return current_file_list

def get_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--cmp_dirs',nargs=2,metavar=('dir1','dir2'),required=True)
    parser.add_argument('-n','--nameID',dest="nameID",help='tag name for compare (used in output filename)')
    parser.add_argument('-vt','--verbose_tar', help='include names of differing files witin tar files', action='store_true',default=False)
    parser.add_argument('-gjf','--get_job_files',nargs=2,metavar=('job','yml_file'),help='capture job level file lists and save in yml_file', required=False)
    args = parser.parse_args()
    for dirs in args.cmp_dirs:
        if not Path(dirs).is_dir():
            logger.critical('directory %s does not exsist'%dirs)
            sys.exit(-1)
    return args

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

    logger,logger_hdr = get_logger()
    args = get_args()

    process_time = time.process_time()

    folder1 = os.path.realpath( args.cmp_dirs[0] )
    folder2 = os.path.realpath( args.cmp_dirs[1] )
    verbose = args.verbose_tar

    if args.get_job_files is not None:
        current_file_list = collections.defaultdict(list)
        current_file_list[args.get_job_files[0]] = capture_files_dir( folder1 )
        with open(args.get_job_files[1], 'w') as outfile:
            yaml.dump(current_file_list, outfile, default_flow_style=False)

    if args.nameID:
        now_date_time  = ''; nameID = args.nameID
        diff_file_name = 'diff_file_list_%s.lst'%nameID
    else:
        now_date_time  = datetime.datetime.now().strftime('%d-%m-%Y-H%H')
        nameID = ''
        diff_file_name = 'diff_file_list_%s.lst'%now_date_time
    diff_file_number = 0
    while os.path.exists(diff_file_name):
        diff_file_number += 1
        diff_file_name = 'diff_file_list_%s%s(%s).lst'%(nameID,now_date_time,str(diff_file_number))

    for folder in (folder1,folder2):
        if not os.path.isdir(folder):
            logger.critical(logger_hdr+'directory %s does not exsist'%folder)
            sys.exit(-1)

    fixed_dir_experment_name = 'fv3gfs_regression_experments'
    cwd = os.getcwd()

    logger.info(logger_hdr+'comparing folders:\n   %s\n   %s'%(folder1,folder2))
    logger.info(logger_hdr+'checking for matching file counts in directories')

    results = compare(folder1, folder2)
    left_right = ('left','right')
    for each_side in left_right:
        if len(results[each_side]) != 0:
            if each_side == 'left':
                foldera = folder1; folderb = folder2
            else:
                folderb = folder1; foldera = folder2
            loggin.info('list of files found in %s and not in %s:'%(os.path.basename(foldera),os.path.basename(folderb)))
            for file in results[each_side]:
                loggin.info('  %s'%file)

    compare_files = filecmp.dircmp(folder1, folder2)
    logger.info(logger_hdr+'checking tar and NetCDF files differences')
    diff_file = open( diff_file_name, 'w')
    print_diff_files( compare_files )
    elapsed_time = time.process_time() - process_time 
    logger.ingo(logger_hdr+'comparing fv3gfs output directories completed. Time to process(%.4f seconds)'%elapsed_time)
    diff_file.close()
