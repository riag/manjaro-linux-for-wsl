
import subprocess
import os
import re
import io
import sys
from urllib import request

import click

core_repo_package_pattern = re.compile(r'^.*?<a\s+[^>]*?href="([^\"]*?)".*?$')
package_name_pattern = re.compile(r'(.*?)-([\d\-\.:]*)-(any|x86_64).*\.(xz|gz)')

DEFAULT_REPO_URL = "http://repo.manjaro.org.uk"
DEFAULT_ARM_REPO_URL = "http://mirror.archlinuxarm.org"
DEFAULT_BRANCH = "stable"

current_dir = os.path.abspath(os.getcwd())
script_dir = os.path.abspath(os.path.dirname(__file__))

default_build_dir = os.path.join(script_dir, 'build')
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
    def __init__(self, work_dir, branch, arch=None):
        self.work_dir = work_dir

        self.arch = arch
        self.branch = branch

        self.repo_url = ''
        self.core_repo_url = ''
        if self.arch.startswith('arm'):
            self.set_repo_url(DEFAULT_ARM_REPO_URL)
        else:
            self.set_repo_url(DEFAULT_REPO_URL)


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
    def __init__(self, name, version, file_name):
        self.name = name
        self.version = version
        self.file_name = file_name


ignore_package = ('../', 'core.db', 'core.db.tar.gz', 'core.files', 'core.files.tar.gz')

def fetch_packages_list(context: BootstrapContext):
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
        p = PackageInfo(name, version, package)
        t = package_map.get(name, None)
        if t is not None:
            print("package %s is already exist" % package)
            sys.exit(-1)

        package_map[name] = p

    return package_map


@click.command()
@click.option('-a','--arch', default='x86_64')
@click.option('-r', '--repo', default='https://mirrors.tuna.tsinghua.edu.cn/manjaro')
@click.option('-w', '--work-dir', default=default_build_dir)
def main(arch, repo, work_dir):
    context = BootstrapContext(work_dir, DEFAULT_BRANCH, arch)
    context.set_repo_url(repo)
    fetch_packages_list(context)


if __name__ == '__main__':
    main()
