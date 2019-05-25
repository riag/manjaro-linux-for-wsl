# coding=utf-8

import click
import os
import io
import sys

import pybee
from pybee.path import working_dir

current_dir = os.path.abspath(os.getcwd())
script_dir = os.path.abspath(os.path.dirname(__file__))

#default_build_dir = os.path.join(script_dir, 'build')
default_build_dir = os.path.expanduser('~/manjaro-linux-wsl-build')
dist_dir = os.path.join(script_dir, 'dist')

work_dir = ''
download_dir = ''
linux_dest_dir = ''

dist_file_name=''

def prepare(arg_work_dir, arch):
    global download_dir
    global linux_dest_dir
    global dist_file_name
    global work_dir

    work_dir = arg_work_dir
    download_dir = os.path.join(work_dir,
            arch, 'download'
            )
    linux_dest_dir = os.path.join(work_dir,
            arch, 'wsl-dist', 'root.%s' % arch
            )

    dist_file_name = 'manjaro-linux-wsl-%s-%s.tar.gz' % (
            arch, pybee.get_curr_date_time('%Y-%m-%d')
            )

    pybee.path.mkdir(download_dir, True)
    pybee.path.mkdir(linux_dest_dir, True)
    pybee.path.mkdir(dist_dir, False)

    pybee.shell.exec(
            ['chmod', '+x',
                './manjaro-bootstrap/manjaro-bootstrap.sh'
            ]
            )


def make_bootstrap_with_shell(arch, repo):
    cmd_list = [
            './manjaro-bootstrap/manjaro-bootstrap.sh',
            '-a', arch,
            '-r', repo,
            '-d', download_dir,
            linux_dest_dir
            ]
    pybee.shell.exec(
            cmd_list
            )

def make_bootstrap(arch, repo):
    cmd_list = [
            sys.executable,
            os.path.join(script_dir, 'manjaro-bootstrap.py'),
            '-a', arch,
            '-r', repo,
            '-d', download_dir,
            '-w', work_dir,
            '--pkg', 'packages.txt'
            ]
    pybee.shell.exec(
            cmd_list
            )

def append_text_to_file(fpath, text, encoding='utf-8'):
    with io.open(fpath, 'a',encoding=encoding) as f:
        f.write(text)

def exec_command_in_chroot_env(dest_dir, cmd, **kwargs):
    chroot_cmd_list = ['chroot', dest_dir, ]
    c = None
    if type(cmd) is str:
        chroot_cmd_list.append(cmd)
        c = ' '.join(chroot_cmd_list)
    else:
        chroot_cmd_list.extend(cmd)
        c = chroot_cmd_list

    pybee.shell.exec(c, **kwargs)

def make_wsl_linux_dist():

#     append_text_to_file(
#             os.path.join(linux_dest_dir, 'etc', 'locale.gen'),
#             '\nen_US.UTF-8 UTF-8'
#             )
#     exec_command_in_chroot_env(linux_dest_dir, ['locale-gen'])

    with working_dir(os.path.join(script_dir, 'configs', 'profile.d')):
        pybee.path.copyfiles(
                ['display.sh', 'wsl.sh'],
                os.path.join(linux_dest_dir, 'etc', 'profile.d')
                )

    '''
    pybee.path.save_text_file(
            os.path.join(linux_dest_dir, 'etc', 'sudoers'),
            'Defaults lecture_file = /etc/sudoers.lecture'
            )
    pybee.path.save_text_file(
            os.path.join(linux_dest_dir, 'etc', 'sudoers.lecture'),
            'Enter your UNIX password below. This is not your Windows password.'
            )
    '''

    exec_command_in_chroot_env(
            linux_dest_dir, ['pacman', '-Scc' ],
            input='yes\nyes\n'.encode('utf-8')
            )

    pybee.sed.replace_by_pattern_list(
        os.path.join(linux_dest_dir, 'usr', 'share', 'dbus-1', 'session.conf'),
        (
            ('^(\s+)<listen>.*</listen>',
             '\g<1><listen>tcp:host=localhost,port=0</listen>'),
            ('^(\s+)<auth>EXTERNAL</auth>', '\g<1><auth>ANONYMOUS</auth>'),
            ('^</busconfig>', '  <allow_anonymous/>\n</busconfig>'),
        )
    )


def pack():

    print('')
    print('tar %s .....' % linux_dest_dir)
    p = os.path.join(dist_dir, dist_file_name)
    if os.path.isfile(p):
        os.unlink(p)

    cwd_dir = os.path.dirname(linux_dest_dir)
    with working_dir(cwd_dir):
        cmd = ' '.join(
                ['tar', '--ignore-failed-read',
                    '-czvf', p, '*']
                )
        pybee.shell.exec(
                cmd, shell=True
                )
    print('finish, dist file is %s' % p)

@click.command()
@click.option('-a','--arch', default='x86_64')
@click.option('-r', '--repo', default='https://mirrors.tuna.tsinghua.edu.cn/manjaro')
@click.option('-w', '--work-dir', default=default_build_dir)
def main(arch, repo, work_dir):

    prepare(work_dir, arch)

    make_bootstrap(arch, repo)

    make_wsl_linux_dist()

    pack()

if __name__ == '__main__':
    main()
