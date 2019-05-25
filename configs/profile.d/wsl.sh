#!/bin/sh

IS_WSL="false"
if [ -n "`grep -i microsoft /proc/version`" ];then
  IS_WSL="true"
fi

export IS_WSL


winenv_path=~/.winenv.sh

function update-winenv(){
    local f="$winenv_path"
    [ -f "$f" ] && rm -f "$f" 
    touch "$f"

    echo "generate $f ....."
    local p=`pywslpath -u --home`
    echo "export WINHOME=\"$p\"" >> "$f"

    p=`pywslpath -u --appdata`
    echo "export APPDATA=\"$p\"" >> "$f"

    p=`pywslpath -u --localappdata`
    echo "export LOCALAPPDATA=\"$p\"" >> "$f"

    p=`pywslpath -u --desktop`
    echo "export WINDESKTOP=\"$p\"" >> "$f"

    p=`pywslpath -u --program-files`
    echo "export PROGRAMFILES=\"$p\"" >> "$f"

    p=`pywslpath -u --temp`
    echo "export WINTEMP=\"$p\"" >> "$f"

    p=`pywslpath -u --sysdir`
    echo "export WINSYSDIR=\"$p\"" >> "$f"

    p=`pywslpath -u --windir`
    echo "export WINDOWDIR=\"$p\"" >> "$f"

    p=`pywslpath -u --programdata`
    echo "export PROGRAMDATA=\"$p\"" >> "$f"

    echo "load $f file"
    source "$f"

    if [ "$SHELL" = '/usr/bin/zsh' ];then
        f=~/.zprofile
        [ -f "$f" ] && rm -f "$f" 
        touch "$f"
        echo "generate $f ....."

        echo "hash -d winhome=\$WINHOME" >> "$f"
        echo "hash -d appdata=\$APPDATA" >>"$f"
        echo "hash -d localappdata=\$LOCALAPPDATA" >> "$f"
        echo "hash -d windesktop=\$WINDESKTOP" >> "$f"
        echo "hash -d programfiles=\$PROGRAMFILES" >>"$f"
        echo "hash -d wintemp=\$WINTEMP" >>"$f"
        echo "hash -d winsysdir=\$WINSYSDIR" >>"$f"
        echo "hash -d windowdir=\$WINDOWDIR" >>"$f"
        echo "hash -d programdata=\$PROGRAMDATA" >>"$f"
    fi
}

if [ -f "$winenv_path" ]; then
	source "$winenv_path"
else
	update-winenv
fi

local dbus_p="/var/lib/dbus/machine-id"
if [ ! -f "$dbus_p" ]; then
  dbus-uuidgen > "$dbus_p"
fi


function print-wsl-info(){
  if [ -n "$WSL_DISTRO_NAME" ];then
    echo "wsl distro name: $WSL_DISTRO_NAME"
  fi

  if [ -n "$WSL_DISTRO_GUID" ];then
    echo "wsl distro guid: $WSL_DISTRO_GUID"
  fi

  if [ -n "$WSL_DISTRO_ROOTFS_DIR" ];then
    echo "wsl distro dir: $WSL_DISTRO_ROOTFS_DIR"
  fi
}


function wopen(){
	if [ "$1" = "--help" ];then
		pywslpath $1
		return
	fi
	local dest_path="$1"
	if [ -z "$dest_path" ];then
		dest_path=`pwd`
	fi
	p=`pywslpath -w -d $dest_path`
	powershell.exe start "\"$p\""
}

function wopen-wsl-home(){
  if [ -z "$WSL_DISTRO_ROOTFS_DIR" ];then
    echo "please define WSL_DISTRO_ROOTFS_DIR env"
    return
  fi
  wopen $WSL_DISTRO_ROOTFS_DIR
}

function wcd(){
  if [ -n "$1" ];then
    p=`pywslpath -u $1`
    cd $p
  fi
}


function find-vscode(){
  if [ -n "$VSCODE_BIN" ];then
    echo "$VSCODE_BIN"
    return
  fi
  local code_bin="`which code`"
  if [ -n "$code_bin" ];then
    echo "$code_bin"
    return
  fi
  code_bin="$LOCALAPPDATA/Programs/Microsoft VS Code/bin/code"
  if [ -f "$code_bin" ];then
    echo "$code_bin"
    return
  fi
  code_bin="$LOCALAPPDATA/Programs/Microsoft VS Code Insiders/bin/code"
  if [ -f "$code_bin" ];then
    echo "$code_bin"
    return
  fi
  echo ""
}

function vc(){
  local code_bin=$(find-vscode)
  if [ -z "$code_bin" ];then
    echo "not found code"
    return
  fi
  local p="$1"
  if [ -z "$p" ];then
    p="`pwd`"
  fi
  local p="`pywslpath -w -d $p`"
  "$code_bin" -r "$p"
}

function vcn(){
  local code_bin=$(find-vscode)
  if [ -z "$code_bin" ];then
    echo "not found code"
    return
  fi
  local p="$1"
  if [ -z "$p" ];then
    p="`pwd`"
  fi
  local p="`pywslpath -w -d $p`"
  "$code_bin" -n "$p"
}
