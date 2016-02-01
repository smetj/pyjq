#!/usr/bin/env python
import io
import os
import subprocess
import tarfile
import shutil
from setuptools import setup
from distutils.extension import Extension
from distutils.command.build_ext import build_ext
from distutils.command.sdist import sdist as _sdist

try:
    import sysconfig
except ImportError:
    # Python 2.6
    from distutils import sysconfig

long_description = io.open('README.rst', encoding='utf-8').read()

try:
    from urllib import urlretrieve
except ImportError:
    from urllib.request import urlretrieve


def path_in_dir(relative_path):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), relative_path))


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


jq_lib_tarball_path = path_in_dir("_jq-lib-1.5.tar.gz")
jq_lib_dir = path_in_dir("jq-jq-1.5")

oniguruma_lib_tarball_path = path_in_dir("_onig-5.9.6.tar.gz")
oniguruma_lib_build_dir = path_in_dir("onig-5.9.6")
oniguruma_lib_install_dir = path_in_dir("onig-install-5.9.6")


class sdist(_sdist):
    def run(self):
        # Make sure the compiled Cython files in the distribution are up-to-date
        from Cython.Build import cythonize
        cythonize(['pyjq.pyx'])
        _sdist.run(self)


class jq_build_ext(build_ext):
    def run(self):
        self._build_oniguruma()
        self._build_libjq()
        build_ext.run(self)

    def _build_oniguruma(self):
        self._build_lib(
            source_url="https://github.com/kkos/oniguruma/releases/download/v5.9.6/onig-5.9.6.tar.gz",
            tarball_path=oniguruma_lib_tarball_path,
            lib_dir=oniguruma_lib_build_dir,
            commands=[
                ["./configure", "CFLAGS=-fPIC", "--prefix=" + oniguruma_lib_install_dir],
                ["make"],
                ["make", "install"],
            ])

    def _build_libjq(self):
        self._build_lib(
            source_url="https://github.com/stedolan/jq/archive/jq-1.5.tar.gz",
            tarball_path=jq_lib_tarball_path,
            lib_dir=jq_lib_dir,
            commands=[
                ["autoreconf", "-i"],
                ["./configure", "CFLAGS=-fPIC", "--disable-maintainer-mode", "--with-oniguruma=" + oniguruma_lib_install_dir],
                ["make"],
            ])

    def _build_lib(self, source_url, tarball_path, lib_dir, commands):
        self._download_tarball(source_url, tarball_path)

        macosx_deployment_target = sysconfig.get_config_var("MACOSX_DEPLOYMENT_TARGET")
        if macosx_deployment_target:
            os.environ['MACOSX_DEPLOYMENT_TARGET'] = macosx_deployment_target

        def run_command(args):
            print("Executing: %s" % ' '.join(args))
            subprocess.check_call(args, cwd=lib_dir)

        for command in commands:
            run_command(command)

    def _download_tarball(self, source_url, tarball_path):
        if os.path.exists(tarball_path):
            os.unlink(tarball_path)
        urlretrieve(source_url, tarball_path)

        if os.path.exists(jq_lib_dir):
            shutil.rmtree(jq_lib_dir)
        tarfile.open(tarball_path, "r:gz").extractall(path_in_dir("."))


pyjq = Extension(
    "pyjq",
    sources=["pyjq.c"],
    include_dirs=[jq_lib_dir],
    extra_objects=[
        os.path.join(jq_lib_dir, ".libs/libjq.a"),
        os.path.join(oniguruma_lib_install_dir, "lib/libonig.a"),
    ],
)

setup(
    install_requires=['six'],
    test_suite='test_pyjq',
    ext_modules=[pyjq],
    cmdclass={
        "build_ext": jq_build_ext,
        "sdist": sdist
    },
    name='pyjq',
    version='1.1',
    description='Binding for jq JSON processor.',
    long_description=long_description,
    author='OMOTO Kenji',
    url='http://github.com/doloopwhile/pyjq',
    license='MIT License',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: JavaScript',
    ],
)
