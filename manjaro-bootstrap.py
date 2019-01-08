
import subprocess
import os
import re
import io
import sys
from urllib import request
import datetime
import json
import shutil

import click

#os.environ['LC_ALL'] = 'C'

core_repo_package_pattern = re.compile(r'^.*?<a\s+[^>]*?href="([^\"]*?)".*?$')
package_name_pattern = re.compile(r'([A-Za-z].*?)-(\d[\w\-\.:+]*)-(any|x86_64).*\.(xz|gz)')
package_update_time_pattern = re.compile(r'(\d+\-\w+\-\d+\s\d+\:\d+)')

update_time_fmt = '%d-%b-%Y %H:%M'

DEFAULT_REPO_URL = "http://repo.manjaro.org.uk"
DEFAULT_ARM_REPO_URL = "http://mirror.archlinuxarm.org"
DEFAULT_BRANCH = "stable"


BASIC_PACKAGES = (
  'libunistring', 'zstd', 'libidn2', 'acl', 'archlinux-keyring',
  'attr', 'bzip2', 'curl', 'expat', 'glibc', 'gpgme', 'libarchive',
  'libassuan', 'libgpg-error', 'libnghttp2', 'libssh2', 'lzo',
  'openssl', 'pacman', 'xz', 'zlib',
  'krb5', 'e2fsprogs', 'keyutils', 'libidn', 'gcc-libs', 'lz4',
  'libpsl', 'icu', 'filesystem'
)

current_dir = os.path.abspath(os.getcwd())
script_dir = os.path.abspath(os.path.dirname(__file__))

default_build_dir = os.path.expanduser('~/manjaro-linux-wsl-build')
default_download_dir = os.path.join(default_build_dir, 'download')
dist_dir = os.path.join(script_dir, 'dist')


def execute_shell_command(cmd_list, work_dir=None):
    print("exec: ", ' '.join(cmd_list))
    output = subprocess.check_output(cmd_list, cwd=work_dir)
    return output


def call_shell_command(cmd_list, work_dir=None, check=True, shell=False):
    if isinstance(cmd_list, (list, tuple)):
        print("exec: ", ' '.join(cmd_list))
    else:
        print("exec: ", cmd_list)
    return subprocess.run(
        cmd_list, check=check, shell=shell,
        cwd=work_dir)


class PipeCommand(object):
    def __init__(self, cmd_list, **kw):
        self.cmd_list = cmd_list
        self.kw = kw


def pipe_call_shell_command(pipe_cmd_list):
    pre_stdout = subprocess.PIPE
    last_p = None
    for cmd in pipe_cmd_list:
        kw = cmd.kw
        kw['stdin'] = pre_stdout
        kw['stdout'] = subprocess.PIPE
        p = subprocess.Popen(
            cmd.cmd_list, **kw
        )
        pre_stdout = p.stdout
        last_p = p

    last_p.wait()


class BootstrapContext(object):
    def __init__(self, work_dir, download_dir, branch, arch=None):
        self.work_dir = work_dir
        self.download_dir = download_dir
        self.dest_dir = os.path.join(work_dir, 'wsl-dist', 'root.%s' % arch)

        self.debug = False

        call_shell_command(
            ['mkdir', '-p', self.dest_dir]
        )
        call_shell_command(
            ['mkdir', '-p', self.download_dir]
        )

        self.arch = arch
        self.branch = branch

        self.base_repo_url = ''
        self.repo_url = ''
        self.core_repo_url = ''
        if self.arch.startswith('arm'):
            self.set_repo_url(DEFAULT_ARM_REPO_URL)
        else:
            self.set_repo_url(DEFAULT_REPO_URL)

        self.core_package_map = {}


    def set_repo_url(self, repo):
        if self.arch.startswith('arm'):
            self.base_repo_url = repo
            self.repo_url = '%s/%s' % (repo, self.arch)
            self.core_repo_url = '%s/%s/%s' % (
                self.base_repo_url, self.arch, 'core'
                )
        else:
            self.base_repo_url = repo
            self.repo_url = '%s/%s/%s/%s' % (
                repo, self.branch, '$repo', self.arch
            )
            self.core_repo_url = '%s/%s/%s/%s' % (
                self.base_repo_url, self.branch, 'core', self.arch
                )


def fetch(context: BootstrapContext):
    output = execute_shell_command(
        ['curl', '-L', '-s', context.core_repo_url]
    )
    if output is None:
        return None

    output = output.decode('utf-8')
    p = os.path.join(context.work_dir, '%s-core.repo' % context.arch)
    with io.open(p, 'w', encoding='utf-8') as f:
        f.write(output)

    return output


class PackageInfo(object):
    def __init__(self, name, version, file_name, update_time):
        self.name = name
        self.version = version
        self.file_name = file_name
        self.update_time = update_time

    def to_map(self):
        m = {
            'name': self.name,
            'version': self.version,
            'file_name': self.file_name,
            #'update_time': self.update_time.time()
        }
        return m


ignore_package = ('../', 'core.db', 'core.db.tar.gz', 'core.files', 'core.files.tar.gz')


def fetch_packages(context: BootstrapContext):
    output = fetch(context)
    sio = io.StringIO(output)
    package_map = {}
    for line in sio:
        if not line:
            continue
        match = core_repo_package_pattern.search(line)
        if match is None:
            continue

        package = match.group(1)
        if package in ignore_package:
            continue
        if package.endswith('.sig'):
            continue

        package = request.unquote(package)
        match = package_name_pattern.search(package)
        if match is None:
            print("cannot parse package name %s" % package)
            sys.exit(-1)

        name = match.group(1)
        version = match.group(2)

        match = package_update_time_pattern.search(line)
        if match is None:
            print("cannot parse package update time, line is %s" % line)
            sys.exit(-1)
        update_time_str = match.group(1)
        update_time = datetime.datetime.strptime(
            update_time_str, update_time_fmt
            )

        t = package_map.get(name, None)
        #if t is not None and update_time < t.update_time:
        #    continue
        if t is not None and version < t.version:
            continue

        p = PackageInfo(name, version, package, update_time)
        package_map[name] = p

    path = os.path.join(context.work_dir, 'core.pakcages.json')
    with io.open(path, 'w', encoding='utf-8') as f:
        m = {}
        for k, v in package_map.items():
            m[k] = v.to_map()
        json.dump(m, f)

    context.core_package_map = package_map
    return package_map


def fetch_file(filepath, url):
    if os.path.exists(filepath):
        print("%s is already exist" % filepath)
        return

    tmp_file = filepath + '.tmp'
    call_shell_command(
        ['curl', '-L', '-o', tmp_file, url]
    )
    os.rename(tmp_file, filepath)


def uncompress(filepath, dest_dir):
    if filepath.endswith('gz'):
        call_shell_command(
            ['tar', 'xfz', filepath, '-C', dest_dir]
        )
        return
    elif filepath.endswith('xz'):
        pipe_call_shell_command(
            [
                PipeCommand(['xz', '-dc', filepath]),
                PipeCommand(['tar', 'x', '-C', dest_dir])
            ]
        )
        return

    print("Error: unknown package format: $s" % filepath)
    sys.exit(-1)


def install_pacman_packages(context: BootstrapContext, package_name_list):
    for name in package_name_list:
        package_info = context.core_package_map.get(name, None)
        if package_info is None:
            print("not support package name %s in core repo" % name)
            sys.exit(-1)

        filepath = os.path.join(context.download_dir, package_info.file_name).replace(':', '-')
        package_url = context.core_repo_url + '/' + package_info.file_name
        fetch_file(filepath, package_url)

        uncompress(filepath, context.dest_dir)


def write_text_to_file(filepath, text):
    with io.open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)


def append_text_to_file(fpath, text, encoding='utf-8'):
    with io.open(fpath, 'a',encoding=encoding) as f:
        f.write(text)

def configure_pacman(context: BootstrapContext):
    print("configure DNS and pacman")
    shutil.copyfile(
        '/etc/resolv.conf',
        os.path.join(context.dest_dir, 'etc', 'resolv.conf')
        )

    pacman_d_dir = os.path.join(context.dest_dir, 'etc', 'pacman.d')
    call_shell_command(
        ['mkdir', '-p', pacman_d_dir]
    )
    write_text_to_file(
        os.path.join(pacman_d_dir, 'mirrorlist'),
        'Server = %s' % context.repo_url
    )


def configure_minimal_system(context: BootstrapContext):
    call_shell_command(
        ['mkdir', '-p', os.path.join(context.dest_dir, 'dev')]
    )
    call_shell_command(
        ['touch', os.path.join(context.dest_dir, 'etc', 'group')]
    )
    write_text_to_file(
        os.path.join(context.dest_dir, 'etc', 'shadow'),
        'root:$1$GT9AUpJe$oXANVIjIzcnmOpY07iaGi/:14657::::::'
    )
    write_text_to_file(
        os.path.join(context.dest_dir, 'etc', 'hostname'),
        'bootstrap'
    )

    pacman_config_path = os.path.join(context.dest_dir, 'etc', 'pacman.conf')
    call_shell_command([
        'sed', '-i', 's/^[[:space:]]*\(CheckSpace\)/# \1/',
        pacman_config_path
        ])
    call_shell_command([
            'sed', '-i', 's/^[[:space:]]*SigLevel[[:space:]]*=.*$/SigLevel = Never/',
            pacman_config_path
        ])

    # coy cert
    name = 'ca-certificates.crt'
    shutil.copyfile(
        './certs/%s' % name,
        os.path.join(context.dest_dir, 'etc', 'ssl', 'certs', name)
    )

    # copy os-release, issue
    for name in ('os-release', 'issue'):
        shutil.copyfile(
            './configs/%s' % name,
            os.path.join(context.dest_dir, 'etc', name)
        )

def configure_locale(context: BootstrapContext):

    append_text_to_file(
        os.path.join(context.dest_dir, 'etc', 'locale.gen'),
        '\nen_US.UTF-8 UTF-8\n'
    )
    call_shell_command([
        'chroot', context.dest_dir, 'locale-gen'
    ])


def install_packages(context: BootstrapContext, package_list):

    print("install package: ")
    print(package_list)

    cmd_list = ['chroot', context.dest_dir, '/usr/bin/pacman',
        '--noconfirm', '--arch', context.arch, '-Sy',
        '--overwrite', '\'*\'', '--force']
    if context.debug:
        cmd_list.append('--debug')
    cmd_list.extend(package_list)
    #cmd_list = 'chroot %s /usr/bin/pacman --noconfirm --arch %s' % (
    #    context.dest_dir, context.arch
    #)
    #cmd_list = cmd_list + ' -Sy --overwrite \'*\' ' + ' '.join(package_list)
    call_shell_command(cmd_list, check=True, shell=False)


def load_package_file(filepath):
    pkg_list = []
    with io.open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line .startswith('#'):
                continue
            pkg_list.append(line)

    return pkg_list


@click.command()
@click.option('-a', '--arch', default='x86_64')
@click.option('-r', '--repo', default='https://mirrors.tuna.tsinghua.edu.cn/manjaro')
@click.option('-w', '--work-dir', default=default_build_dir)
@click.option('--download-dir', default=default_download_dir)
@click.option('--pkg', 'package_file', required=True)
@click.option('--debug', flag=True, default=False)
def main(arch, repo, work_dir, download_dir, package_file, debug):

    context = BootstrapContext(
        work_dir, download_dir,
        DEFAULT_BRANCH, arch)
    context.set_repo_url(repo)
    context.debug = debug

    fetch_packages(context)

    install_pacman_packages(context, BASIC_PACKAGES)

    configure_pacman(context)
    configure_minimal_system(context)

    install_packages(context, BASIC_PACKAGES)

    # 不知道为啥 grep file 这 2 个包不能安装
    install_packages(context,
        ('bash', 'gawk', 'sed', 'tar',
        'manjaro-release', 'which', 'coreutils',
        'findutils', 'grep', 'file', 'pamac'
        )
    )
    #configure_locale(context)

    # TODO: 安装其他软件
    package_list = load_package_file(package_file)
    install_packages(context, package_list)

    # clean /var/cache/pacman/pkg 下包

    #configure_pacman(context)


if __name__ == '__main__':
    main()
