# TODO refactor, many functions here are quite old and don't use modern Python features
# TODO look into default encoding used by some functions
import glob
import inspect
import os
import sys
from os import path
from shutil import copy as _copyfile

_DIGITS = '0123456789'


def make_dirs(filename):
    dirname = path.dirname(filename)
    if not path.exists(dirname):
        # import errno
        try:
            os.makedirs(dirname)
        except OSError as exc:  # Guard against race condition
            # if exc.errno != errno.EEXIST:
            if not path.exists(dirname):
                raise


def get_free_space_mb(dirname):
    """Return folder/drive free space (in bytes)."""

    import ctypes
    import platform

    if platform.system() == 'Windows':
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(dirname), None, None, ctypes.pointer(free_bytes)
        )
        return free_bytes.value
    else:
        st = os.statvfs(dirname)
        return st.f_bavail * st.f_frsize


def filesize(fname: str) -> int:
    '''File size in bytes'''
    stats = os.stat(fname)
    return stats.st_size


def copy_file(src, dest):
    _copyfile(src, dest)
    '''except shutil.Error as e:
        print(('Error: %s' % e))
    except IOError as e:
        print(('Error: %s' % e.strerror))'''


def show_dirs():
    print('Current path folders:')
    print(sys.path)
    print('Current file:')
    tmp = inspect.getfile(inspect.currentframe())
    print(tmp)
    print('Current directory:')
    tmp = os.path.split(tmp)[0]
    print(tmp)
    print('Directory, once again:')
    cmd_folder = os.path.realpath(os.path.abspath(tmp))
    print(cmd_folder)


def del_files_by_mask(mask: str, include_subdir: bool):
    cnt = 0
    if include_subdir:
        fn_l = get_masked_fnames(mask)
    else:
        fn_l = glob.glob(mask)
    for fn in fn_l:
        os.remove(fn)
        cnt += 1
    return cnt


def f_exists(fn):
    return os.access(fn, os.R_OK)


def replace_in_f(fn, fn_new, st_old, st_new, make_backup=True):
    with open(fn, 'r') as f:
        data = f.read()
    data = data.replace(st_old, st_new)
    if f_exists(fn_new) and make_backup:
        ext = '.bak'
        while f_exists(fn_new + ext):
            ext = ext + 'k'
        os.rename(fn_new, fn_new + ext)
    with open(fn_new, 'w') as f:
        f.write(data)


def find_in_files(st, mask=None, max_per_f=None, line_by_line=True):
    '''Searches for st in individual lines
    in files (including all subdirectories) satisfying mask'''
    f_l = []
    for fn in get_masked_fnames(mask):
        cnt = 0
        for line in get_lines(fn):
            if not line_by_line:
                print(line)
            if st in line:
                if fn not in f_l:
                    f_l.append(fn)
                    print('\n', '-' * 20, 'File:', fn, '-' * 20)
                print(line)
                cnt += 1
                if cnt == max_per_f:
                    break
    return f_l


def split_file(fn, st_l):
    l = len(st_l)
    fn_l = []
    cnt_l = []
    fn0 = fn.split('.')[0]
    for i in range(l):
        fn_l.append(fn0 + str(i) + '.txt')
        cnt_l.append(0)
    fn_l.append(fn0 + '_extra' + '.txt')

    cnt = 0
    n_wr = l
    f_wr = open(fn_l[n_wr], 'a')
    with open(fn, 'r') as f:
        for line in f:
            for i in range(l):
                if st_l[i] in line:
                    # if line.startswith(st_l[i]):
                    cnt_l[i] += 1
                    if i != n_wr:
                        f_wr.close()
                        n_wr = i
                        f_wr = open(fn_l[n_wr], 'a')
                    break
            f_wr.write(line)
            cnt += 1
            if not (cnt % 1000):
                print(cnt, 'lines processed. Chunks breakdown:', cnt_l)
    f_wr.close()
    print('Finished.', cnt, 'lines processed. Chunks breakdown:', cnt_l)


def split_file_ln(fn, n_ln, fn_base='', overwrite=False):
    def new_fn(n):
        fn_ = fn_base + str(n)
        fn_res = pth + fn_ + ext
        if overwrite:
            return fn_res
        nn = 2
        while f_exists(fn_res):
            fn_res = pth + fn_ + '(' + str(nn) + ')' + ext
        return fn_res

    n_wr = 0
    pth, fn0, ext = split_fn(fn)
    if not fn_base:
        fn_base = fn0
    fn_l = [new_fn(n_wr)]
    f_wr = open(fn_l[-1], 'w')
    ln_cnt = 0
    try:
        with open(fn, 'r') as f:
            for line in f:
                f_wr.write(line)
                ln_cnt += 1
                if ln_cnt % n_ln == 0:
                    n_wr += 1
                    fn_l += [new_fn(n_wr)]
                    f_wr.close()
                    f_wr = open(fn_l[-1], 'w')
                if not (ln_cnt % 10000):
                    print(ln_cnt, 'lines processed.')
    finally:
        f_wr.close()
    print('Finished.', end=' ')
    print(ln_cnt, 'lines processed.')


def sort_fns_w_nums(fn_l, only_nums=False):
    def fn_to_tupl(fn):
        dirn, fn00, num_s, ext = split_fn_w_nums(fn)
        if num_s:
            num = int(num_s)
        else:
            num = -1
        if only_nums:
            return num
        else:
            return (dirn, fn00, num, len(num_s), ext)

    return sorted(fn_l, key=fn_to_tupl)


def rename_files(find_st, replace_st, fn_l=None):
    '''Rename files in the specified file name list (or in the current directory)
    by replacing a given substring in their names'''
    cnt = 0
    cnt2 = 0
    if fn_l is None:
        fn_l = glob.glob('*.*')
    try:
        n_tot = len(fn_l)
    except:
        n_tot = '[Unknown number]'
    print(n_tot, 'files found.')
    for fn in fn_l:
        if find_st in fn:
            fn_new = fn.replace(find_st, replace_st)
            os.rename(fn, fn_new)
            cnt2 += 1
        cnt += 1
        if cnt2 > 0 and cnt2 % 1000 == 0:
            print(cnt2, 'files remamed.', cnt, 'of', n_tot, 'files processed,')
    print(cnt2, 'files remamed.', cnt, 'of', n_tot, 'files processed,')


def show_tree():
    root_dir = '.'
    for dir_name, subdir_list, file_list in os.walk(root_dir):
        print(('Found directory: %s' % dir_name))
        for fname in file_list:
            fn_full = dir_name + '\\' + fname
            print(('\t%s' % fn_full))


def get_fnames_fixed_dirs(dir_l):
    f_l = []
    for mypath in dir_l:
        try:
            fn_l = os.listdir(mypath)
        except:
            fn_l = []
        for fn in fn_l:
            fn_full = os.path.join(mypath, fn)
            if os.path.isfile(fn_full):
                f_l.append(fn_full)
                # print os.path.getmtime(fn_full)
                # print datetime.fromtimestamp(os.path.getmtime(fn_full))
    return f_l


def get_fnames_main(root_dir='.', mask=None, incl_subdir=True):
    '''Return file names matching the given mask (or all files), looks in subdirs by default'''
    full_file_l = []
    for dir_cur, subdir_l, file_l in os.walk(root_dir):
        if mask:
            for fn_full in glob.glob(dir_cur + '\\' + mask):
                full_file_l.append(fn_full)
        else:
            for fname in file_l:
                fn_full = os.path.join(dir_cur, fname)
                full_file_l.append(fn_full)
                # yield fn_full
        if not incl_subdir:
            break
    return full_file_l


def get_all_fnames(root_dir='.'):
    return get_fnames_main(root_dir=root_dir)


def get_masked_fnames(mask, root_dir='.'):
    return get_fnames_main(root_dir=root_dir, mask=mask)


def get_masked_fnames_no_subdirs(mask, root_dir='.'):
    # return get_fnames_main(root_dir=root_dir, mask=mask)
    return glob.glob(os.path.join(root_dir, mask))


def get_dir_names(root_dir='.'):
    dir_l = []
    for dir_cur, subdir_list, file_l in os.walk(root_dir):
        dir_l.append(dir_cur)
    return dir_l


def get_dirs(root_dir='.'):
    p = os.path.abspath(root_dir)
    return [os.path.join(p, n) for n in os.listdir(p) if os.path.isdir(os.path.join(p, n))]


def split_fn(fn_full):
    pth, fn = os.path.split(fn_full)
    if pth:
        pth += '\\'
    fn0, ext = os.path.splitext(fn)
    return pth, fn0, ext


def split_fn_w_nums(fn_full):
    pth, fn0, ext = split_fn(fn_full)
    fn00 = fn0.rstrip(_DIGITS)
    num_s = fn0[len(fn00) :]
    return pth, fn00, num_s, ext


def extract_fname(fn_full):
    return os.path.basename(fn_full)


def extract_fn_no_ext(fn_full):
    fn, ext = os.path.splitext(os.path.basename(fn_full))
    return fn


def extract_ext(fn_full):
    fn, ext = os.path.splitext(fn_full)
    return ext


def extract_dir(fn_full):
    return os.path.dirname(fn_full)


def get_txt(fn, encoding='latin1'):
    with open(fn, 'r', encoding=encoding) as f_read:
        return f_read.read()


def write_txt(fn, st, encoding='latin1'):
    with open(fn, 'w', encoding=encoding) as f:
        return f.write(st)


def get_lines(fn, strip_endl=True, encoding='latin1'):
    '''Returns a list of lines, By default removes end of line characters'''
    # https://stackoverflow.com/questions/275018/how-can-i-remove-chomp-a-newline-in-python
    with open(fn, 'r', encoding=encoding) as f_read:
        if strip_endl:
            return [line.rstrip('\n\r') for line in f_read.readlines()]
        else:
            return f_read.readlines()

        # Python two, and wordpad by default replaces \r\n with \n when
        # opening files, and \r\r\n with \r\n, and in either of those
        # cases interprets those two or three symbols as the end of a line.

        # By contrast, Python three and notepad  replaces \r\n with \n when
        # opening files, and \r\r\n with \n\n, And interprets the latter
        # case as two lines with the second line being empty


def get_lines_g(fn, strip_endl=True, encoding='latin1'):
    '''Returns a list of lines, By default removes end of line characters'''
    # https://stackoverflow.com/questions/275018/how-can-i-remove-chomp-a-newline-in-python
    with open(fn, 'r', encoding=encoding) as f_read:
        for line in f_read:
            if strip_endl:
                yield line.rstrip('\n\r')
            else:
                yield line


def add_line(fn, line, add_endl=True, mode='a'):
    with open(fn, mode) as f_wr:
        f_wr.write(line)
        if add_endl:
            f_wr.write('\r\n')


def add_lines(fn, line_l, add_endl=True, mode='a'):
    with open(fn, mode) as f_wr:
        for line in line_l:
            f_wr.write(line)
            if add_endl:
                f_wr.write('\r\n')


def compare_files(fn1, fn2):
    with open(fn1, 'rb') as f1:
        with open(fn2, 'rb') as f2:
            cnt = 0
            while True:
                b1 = f1.read(1)
                b2 = f2.read(1)
                if not b1 or b1 != b2:
                    break
                cnt += 1
            if b1 == b2:
                print('Files are identical.')
                return
            print('First', cnt, 'bytes are identical.')
            print('The next byte from the first file:', b1, '(', ord(b1), ')')
            print('The next byte from the second file:', b2, '(', ord(b2), ')')
            return


def compare_txt_files(fn1, fn2, n_to_ck=0):
    line1_l = get_lines(fn1, strip_endl=False)
    line2_l = get_lines(fn2, strip_endl=False)
    cnt = 0
    n1 = len(line1_l)
    n2 = len(line2_l)
    nmax = max(n1, n2)
    nmin = min(n1, n2)
    if not n_to_ck:
        n_to_ck = nmax
    else:
        n_to_ck = min(nmax, n_to_ck)
    if nmin < n_to_ck:
        print(n1)
        print(n2)
        return False
    for s1, s2 in zip(line1_l, line2_l):
        if s1 != s2:
            print(s1)
            print(s2)
            return False
        cnt += 1
        if cnt == n_to_ck:
            break
    return True


if __name__ == '__main__':
    i = 0
