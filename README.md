# manjaro-linux-for-wsl
为 windows 10 WSL 而做的 Manjaro Linux 发行版本

该项目是基于 [manjaro-bootstrap]() 而做的，该发行版本只打包了最基本的软件

## 分支说明
  官方维护的 manjaro-bootstrap 有一些 bug，所以把原代码复制到分支 `manjaro-bootstrap` 下，`master`分支是 fix bug 后的代码

## 下载

TODO: 提供已经打包好的压缩文件



## 使用

下载 tar 文件后，建议使用 [LxRunOffline](https://github.com/DDoSolitary/LxRunOffline) 来安装，可以使用下面命令来安装

```
LxRunOffline.exe install -n manjaro-linux -f ../manjaro-linux-wsl-x86_64-2018-11-05.tar.gz -d G:\devel\wsl\manjaro-linux -r root.x86_64
```

**注意** 要修改上面安装命令的参数要实际的值

## 打包

  打包脚本采用 Python 语言开发

### 依赖软件
  安装以下工具
* [Python 3.5+](https://www.python.org/)
* [python-pipenv](https://github.com/pypa/pipenv) 

#### 安装依赖包
  使用以下命令安装依赖包
  ```
pipenv install --dev
  ```

### 打包
  使用以下命令打包
 ```
pipenv run python3 build.py -a x86_64 -w ~/manjaro-linux-rootfs
 ```

 **注意**: 第一次执行该命令时，会卡在一个地方(见下图)，直接按 `Ctrl+C` 中断打包过程，再执行一次该命令就好了

![](./images/pack-error.png)

 打包成功后，压缩文件放在 `当前目录/dist` 目录下

## 参数说明

```
-a/--arch       CPU 架构，默认是 x86_64
-r/--repo       下载依赖包的 repo，默认是 https://mirrors.tuna.tsinghua.edu.cn/manjaro
-w/--work-dir   指定工作目录，默认是 当前目录/build 
```
