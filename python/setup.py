import os
import subprocess
import sys
import glob
from pathlib import Path
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext as _build_ext

# Try to import pybind11
try:
    import pybind11
    PYBIND11_AVAILABLE = True
except ImportError:
    PYBIND11_AVAILABLE = False
    print("Warning: pybind11 not found. Installing it first...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pybind11[global]>=2.6.0"])
    import pybind11

# --- Windows 符号链接修复逻辑 ---
def get_libraries():
    """获取所有需要链接的库名"""
    libs = ["webrtc-audio-processing-2"] # 默认基础库
    # 如果在 Windows 上，自动扫描 ../install/lib 下所有的 .lib 文件
    # 解决 "unresolved external symbol" (LNK2001) 报错
    lib_dir = Path("../install/lib")
    if lib_dir.exists():
        found_libs = [Path(f).stem for f in glob.glob(str(lib_dir / "*.lib"))]
        if found_libs:
            return list(set(found_libs)) # 去重
    return libs

# Define the extension module
ext_modules = [
    Extension(
        "webrtc_audio_processing",
        ["webrtc_audio_processing.cpp"],
        include_dirs=[
            pybind11.get_include(),
            "../install/include",
            "../install/include/webrtc-audio-processing-2",
            "../webrtc",
        ],
        libraries=get_libraries(),
        library_dirs=[
            ".",
            "../install/lib",
            "/usr/local/lib",
        ],
        language='c++',
        define_macros=[("VERSION_INFO", '"dev"')],
    ),
]

class BuildExt(_build_ext):
    def build_extensions(self):
        if not self.check_webrtc_library():
            print("WebRTC Audio Processing library not found.")
            sys.exit(1)

        ct = self.compiler.compiler_type
        opts = []
        link_opts = []

        if ct == 'unix':
            opts.append('-std=c++17')
            if sys.platform != 'darwin':
                link_opts.append(f'-Wl,-rpath,{os.path.abspath("../install/lib")}')
        elif ct == 'msvc':
            opts.append('/std:c++17')
            opts.append('/EHsc') # 确保异常处理开启

        for ext in self.extensions:
            ext.extra_compile_args = opts
            ext.extra_link_args = link_opts
        super().build_extensions()

    def check_webrtc_library(self):
        search_paths = [
            os.path.abspath("../install/lib"),
            "../install/lib",
            "install/lib",
            "/usr/local/lib",
        ]
        library_names = [
            "libwebrtc-audio-processing-2.so",
            "libwebrtc-audio-processing-2.a",
            "libwebrtc-audio-processing-2.dylib",
            "webrtc-audio-processing-2.lib",
            "libwebrtc-audio-processing-2.lib",
        ]
        for path in search_paths:
            for lib_name in library_names:
                if (Path(path) / lib_name).exists():
                    print(f"Found WebRTC library: {Path(path) / lib_name}")
                    return True
        return False

if __name__ == "__main__":
    setup(
        name="webrtc-audio-processing",
        version="2.1.0",
        ext_modules=ext_modules,
        cmdclass={"build_ext": BuildExt},
        zip_safe=False,
    )