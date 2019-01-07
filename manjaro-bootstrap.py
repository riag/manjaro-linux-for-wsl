
import subprocess
import os
import re
import io
import sys
from urllib import request
import datetime
import json

import click

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
  'openssl', 'pacman', 'pacman-mirrors', 'xz', 'zlib',
  'krb5', 'e2fsprogs', 'keyutils', 'libidn', 'gcc-libs', 'lz4',
  'libpsl', 'icu', 'filesystem'
)

current_dir = os.path.abspath(os.getcwd())
script_dir = os.path.abspath(os.path.dirname(__file__))

default_build_dir = os.path.join(script_dir, 'build')
default_download_dir = os.path.join(default_build_dir, 'download')
dist_dir = os.path.join(script_dir, 'dist')


def execute_shell_command(cmd_list, work_dir=None):
    print("exec: ", ' '.join(cmd_list))
    output = subprocess.check_output(cmd_list, cwd=work_dir)
    return output


def call_shell_command(cmd_list, work_dir=None, check=True, shell=False):
    print("exec: ", ' '.join(cmd_list))
    return subprocess.run(
        cmd_list, check=check, shell=shell,
        cwd=work_dir).returncode


class BootstrapContext(object):
    def __init__(self, work_dir, download_dir, branch, arch=None):
        self.work_dir = work_dir

        self.download_dir = download_dir

        self.arch = arch
        self.branch = branch

        self.repo_url = ''
        self.core_repo_url = ''
        if self.arch.startswith('arm'):
            self.set_repo_url(DEFAULT_ARM_REPO_URL)
        else:
            self.set_repo_url(DEFAULT_REPO_URL)

        self.core_package_map = {}


    def set_repo_url(self, repo):
        if self.arch.startswith('arm'):
            self.repo_url = repo
            self.core_repo_url = '%s/%s/%s' % (
                self.repo_url, self.arch, 'core'
                )
        else:
            self.repo_url = repo
            self.core_repo_url = '%s/%s/%s/%s' % (
                self.repo_url, self.branch, 'core', self.arch
                )


def fetch(context: BootstrapContext):
    output = execute_shell_command(
        ['curl', '-L', '-s', context.core_repo_url]
    )
    if output is None:
        return None

    output = output.decode('utf-8')
    p = os.path.join(context.work_dir, 'core_repo.idex')
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
        print("update time %s" % update_time_str)
        update_time = datetime.datetime.strptime(
            update_time_str, update_time_fmt
            )

        t = package_map.get(name, None)
        if t is not None and update_time < t.update_time:
            continue

        print("package is %s, %s" % (name, package))
        p = PackageInfo(name, version, package, update_time)
        package_map[name] = p

    path = os.path.join(context.work_dir, 'core.pakcage.json')
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


def install_pacman_packages(context: BootstrapContext, package_name_list):
    for name in package_name_list:
        package_info = context.core_package_map.get(name, None)
        if package_info is None:
            print("not support package name %s in core repo" % name)
            sys.exit(-1)

        filepath = os.path.join(context.download_dir, package_info.file_name).replace(':', '-')
        package_url = context.core_repo_url + '/' + package_info.file_name
        fetch_file(filepath, package_url)


@click.command()
@click.option('-a', '--arch', default='x86_64')
@click.option('-r', '--repo', default='https://mirrors.tuna.tsinghua.edu.cn/manjaro')
@click.option('-w', '--work-dir', default=default_build_dir)
@click.option('--download-dir', default=default_download_dir)
def main(arch, repo, work_dir, download_dir):

    context = BootstrapContext(work_dir, download_dir, DEFAULT_BRANCH, arch)
    context.set_repo_url(repo)

    fetch_packages(context)

    install_pacman_packages(context, BASIC_PACKAGES)


if __name__ == '__main__':
    main()
