import json
import os
import shutil

import utilsfiles as uf

FILES_TO_SKIP_KEY = 'files to skip'
WORDS_TO_SKIP_KEY = 'words to skip'
WORKING_DIR_KEY = 'directory to find *.py files'
CONFIG_FNAME = 'config.json'  #'Camel to Snake Converter Config.json'
DEFAULT_WORKING_DIR = '..'
FILE_MASK = '*.py'
BKUP_DIR = 'Snakify Backups'  #'Backups from Camel to Snake Converter'

ROLE_WRD, ROLE_NONWRD = 1, 2
DIGITS_SET = set('0123456789')


def make_bkup(fn):
    fn_new = uf.extract_fname(fn)  # + '.bak'  # os.path.splitext(fn)[0] + '.pybak'
    fn_new = os.path.join(working_dir, BKUP_DIR, fn_new)
    while uf.f_exists(fn_new):
        fn_new = input(
            f'File {fn_new} already exists. Enter a different name to back up {fn} to or press Enter to exit. Enter just the file name, not the full path.'
        )
        if not fn_new:
            exit()
        fn_new = os.path.join(BKUP_DIR, fn_new)

    uf.make_dirs(fn_new)
    shutil.copy(fn, fn_new)


def save_settings():
    with open(CONFIG_FNAME, 'w') as f:
        json.dump(
            {
                WORKING_DIR_KEY: working_dir,
                FILES_TO_SKIP_KEY: list(fnames_to_skip),
                WORDS_TO_SKIP_KEY: list(wrds_to_skip),
            },
            f,
        )


def load_settings():
    global fnames_to_skip, wrds_to_skip, working_dir
    try:
        with open(CONFIG_FNAME, 'r') as f:
            settings = json.load(f)
        working_dir = settings[WORKING_DIR_KEY]
        fnames_to_skip = set(settings[FILES_TO_SKIP_KEY])
        wrds_to_skip = set(settings[WORDS_TO_SKIP_KEY])
        return settings
    except FileNotFoundError:
        working_dir = DEFAULT_WORKING_DIR
        fnames_to_skip, wrds_to_skip = set(), set()
        save_settings()
        # input(' settings created '); exit()
        return False


def split_by_role(s: str):
    '''Returns two lists, first is s split by role (identifier, non-identifier), second
    contains roles for each element of the first list ('wrd', 'nwrd')
    '''

    def analyze_role():
        chunk_ended = 0  # 0 - chunk continues, 1, 2,... - chunk ends
        if prev_sym_type & wrd_bit and not (cur_sym_type & wrd_bit):  # wrd ended
            chunk_ended = ROLE_WRD
        elif prev_sym_type & oth_sym_bit and not (cur_sym_type & oth_sym_bit):  # nonwrd ended
            chunk_ended = ROLE_NONWRD
        # if chunk ended update chunk and role lists
        if chunk_ended:
            chunk_l.append(chunk_s)
            role_l.append(chunk_ended)
        return chunk_ended

    empty_sym_bit = 0b0
    alnum_bit = 0b1
    underscore_bit = 0b10
    wrd_bit = alnum_bit | underscore_bit
    oth_sym_bit = 0b100

    chunk_l = []
    role_l = []
    prev_sym_type = empty_sym_bit
    chunk_s = ''
    for c in s:
        # categorize the current character
        if c.isalnum():
            cur_sym_type = alnum_bit
        elif c == '_':
            cur_sym_type = underscore_bit
        else:
            cur_sym_type = oth_sym_bit

        is_new_chunk = analyze_role()
        if is_new_chunk:
            chunk_s = ''
        chunk_s += c
        prev_sym_type = cur_sym_type
    # run chunk analysis one last time, this time with empty symbol '' playing role of c
    cur_sym_type = empty_sym_bit
    assert analyze_role()  # should always complete final chunk
    return chunk_l, role_l


def camel_to_snake(s: str):
    s_new = ''
    # initialize "flags"
    word_with_caps_flg = prev_mult_caps_flg = prev_now_word_flg = prev_cap_flg = False
    c_prev = ''
    for c in s:
        turn_on_mult_caps = False

        now_word_flg = c.isalnum() or c == '_'
        word_beg_flg = not prev_now_word_flg and now_word_flg
        now_cap_flg = c.isupper()

        if word_beg_flg and now_cap_flg:
            word_with_caps_flg = True
        elif not now_word_flg:
            word_with_caps_flg = False

        if word_with_caps_flg:  # don't change words like MyClassWithCaps
            s_new += c
        elif now_cap_flg:
            if prev_cap_flg:
                turn_on_mult_caps = True  # found two caps in a row
            elif c_prev != '_':
                s_new += '_'
            s_new += c.lower()
        elif now_word_flg:  # non-upper but can be part of a variable name
            if prev_mult_caps_flg and c != '_':  # insert underscore
                s_new += '_' + c
            else:
                s_new += c
        else:  # not part of a name
            s_new += c

        # update flags
        prev_cap_flg = now_cap_flg
        prev_mult_caps_flg = turn_on_mult_caps
        prev_now_word_flg = now_word_flg
        c_prev = c

    return s_new


if __name__ == '__main__':
    print('-' * 78)
    print('SNAKEFY: someVarName --> some_var_name')
    print('-' * 78, '\n')
    if settings_d := load_settings():
        print(f'Found {CONFIG_FNAME} and loaded settings from it:')
    else:
        print(
            f'Config file {CONFIG_FNAME} not found (probably because you are running this '
            'for the first time), so I created one for you with default settings:'
        )
        settings_d = load_settings()
    for key, val in settings_d.items():
        print(f'\n{repr(key)}: {repr(val)}')
    print()

    fnames = uf.get_masked_fnames_no_subdirs(FILE_MASK, root_dir=working_dir)
    while True:
        ans = input(
            f'Found {len(fnames)} Python files in directory "{working_dir}". Before making any changes, we should back them up to directory "{BKUP_DIR}". Type "skip" to skip the backup (e.g. if you already made one) or "bkup" to proceed with the backup: '
        )
        if ans in ['skip', 'bkup']:
            break

    print()
    if ans == 'skip':
        print('Skipping backup.')
        ans = 'go'
    else:
        for fn in fnames:
            make_bkup(fn)
        ans = ''
    
    while not ans:
        ans = input(
            f'Done. Please verify that all {len(fnames)} files have been backed up. '
            'Type "go" to '
            'confirm that you are ok with me modifying your files and understand that I can\'t '
            'give you a guarantee that I am bug-free and won\'t mess them up: '
        )
    if ans != 'go':
        exit()

    print()
    for fn in fnames:
        print('-' * 60)
        if fn in fnames_to_skip:
            print(f'File {fn} is on a permanent ignore list, skipping.')
            continue
        print(f'Processing {fn}.\n')
        with open(fn, 'r') as f:
            s = f.read()

        chunk_l, role_l = split_by_role(s)
        new_wrd_d = {}
        seen_wrd_set = set()
        unchanged_wrd_set = set()
        for chunk, role in zip(chunk_l, role_l):
            if role != ROLE_WRD or chunk in seen_wrd_set or chunk in wrds_to_skip:
                continue
            if chunk[0] in DIGITS_SET:  # wrd starting with digit can't be an identifier
                continue
            new_wrd = camel_to_snake(chunk)
            if new_wrd != chunk:
                new_wrd_d[chunk] = new_wrd
            else:
                unchanged_wrd_set.add(chunk)
            seen_wrd_set.add(chunk)

        if not new_wrd_d:
            print('No changes required, moving on.')
            continue

        # check if any proposed changes would create duplicates:
        duplicates_l = []
        for wrdold, wrdnew in new_wrd_d.items():
            if wrdnew in unchanged_wrd_set:
                duplicates_l.append(wrdold)
                new_wrd_d[wrdold] = wrdold

        if duplicates_l:
            print(f'Changing the following words to camelcase would create duplicates:')
            print(', '.join(duplicates_l))
            print('\nTherefore by default they will remain unchanged.\n')

        while True:
            wrdold_l = list(new_wrd_d.keys())
            for i, wrdold in enumerate(wrdold_l):
                wrdnew = new_wrd_d[wrdold]
                tmp = '- UNCHANGED' if wrdnew == wrdold else f'-> {wrdnew}'
                print(f'{i + 1}. {wrdold} {tmp}')
            ans = input(
                '\nType "ok" to implement changes, "s" to skip this file, "never" to never analyze this file again, or the numbers of items to edit (separate them with commas, or type "all" to select all words): '
            )
            if ans in ['ok', 's', 'never']:
                break
            if ans == 'all':
                wrdind_l = list(range(len(wrdold_l)))
            else:
                try:
                    parts = [part.strip() for part in ans.split(',')]
                    wrdind_l = [int(x) - 1 for x in parts]
                except:
                    continue

            if len(wrdind_l) == 1:
                wrd = wrdold_l[wrdind_l[0]]
                tmp = input(
                    f'You selected {wrd}. Enter the new replacement name, press Enter to ignore, or type a period to put it on a permanent ignore list: '
                )
                new_wrd_d[wrd] = wrd if tmp in ['.', ''] else tmp
                if tmp == '.':
                    wrds_to_skip.add(wrd)
                    save_settings()
            else:  # multiple item numbers
                wrds = [wrdold_l[ind] for ind in wrdind_l]
                print(f'You selected: {", ".join(wrds)}')
                tmp = input(
                    'Type "i" to ignore these just in this session, "p" to put them on a permanent ignore list, or anything else to go back to selecting items: '
                )
                if tmp in 'ip':
                    for w in wrds:
                        new_wrd_d[w] = w
                if tmp == 'p':
                    wrds_to_skip.update(wrds)
                    save_settings()

        if ans == 'never':
            fnames_to_skip.add(fn)
            save_settings()
        elif ans == 'ok':
            for i, chunk in enumerate(chunk_l):
                try:
                    chunk_l[i] = new_wrd_d[chunk]
                except KeyError:
                    pass
            with open(fn, 'w') as f:
                f.write(''.join(chunk_l))
