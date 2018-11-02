# coding=utf-8

import re
import io
import subprocess
import click

tag_pkg_pattern = re.compile('^>(\S+)\s+(\S+)(\s+#.*)*')
pkg_pattern = re.compile('^(\S+)(\s+#.*)*')

def load_pkg(fpath):
    pkg_list = []
    with io.open(fpath, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue

            if line.startswith('#'): continue

            t = tag_pkg_pattern.match(line)
            if t:
                pkg_list.append(t.group(2))
            else:
                t = pkg_pattern.match(line)
                if t:
                    pkg_list.append(t.group(1))

    return pkg_list

def install_pkgs(pkg_list):
    for pkg in pkg_list:
        cmd = ['pacman', '--noconfirm', '-S', pkg]
        subprocess.run(cmd)

@click.command()
@click.argument('pkg_files', nargs=-1)
def main(pkg_files):

    for fpath in pkg_files:
        print('starting install package from %s' % fpath)
        pkg_list = load_pkg(fpath)
        print(pkg_list)
        install_pkgs(pkg_list)

if __name__ == '__main__':
    main()
