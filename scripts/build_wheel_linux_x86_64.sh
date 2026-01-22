#!/usr/bin/env bash
set -euo pipefail

# 获取项目根目录
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 如果脚本在 scripts 目录下，则回退一级，如果在根目录则不需要
if [[ "$repo_root" == */scripts ]]; then
    repo_root="$(dirname "$repo_root")"
fi

build_dir="${repo_root}/build-x86_64"
install_dir="${repo_root}/install"
dist_dir="${repo_root}/dist"

host_os="$(uname -s)"
host_arch="$(uname -m)"

# 修改点：放宽架构检查，支持 x86_64
if [[ "${host_os}" != "Linux" || "${host_arch}" != "x86_64" ]]; then
  echo "Error: This script is modified for Linux x86_64."
  echo "Detected: ${host_os} ${host_arch}"
  exit 1
fi

library_present() {
  local lib_dir
  # 修改点：路径适配 x86_64-linux-gnu
  for lib_dir in \
    "${install_dir}/lib" \
    "${install_dir}/lib64" \
    "${install_dir}/lib/x86_64-linux-gnu"; do
    if ls "${lib_dir}"/libwebrtc-audio-processing-2.* >/dev/null 2>&1; then
      return 0
    fi
  done
  return 1
}

# 编译 C++ 核心库
if ! library_present; then
  if ! command -v meson >/dev/null 2>&1; then
    echo "meson not found; please install meson and ninja (pip install meson ninja), then re-run."
    exit 1
  fi

  if [ ! -d "${build_dir}" ]; then
    # 修改点：设置 x86_64 的库路径
    # 这种写法最稳妥：meson setup [目标目录] [源目录] [参数]
    meson setup "${build_dir}" "${repo_root}" --libdir=lib/x86_64-linux-gnu -Dprefix="${install_dir}"
  else
    meson setup --reconfigure "${build_dir}" --libdir=lib/x86_64-linux-gnu -Dprefix="${install_dir}" "${repo_root}"
  fi
  meson compile -C "${build_dir}"
  meson install -C "${build_dir}"
fi

# 打包 Python Wheel
mkdir -p "${dist_dir}"
cd "${repo_root}/python"

echo "Building Python wheel..."
if python3 -m build --version >/dev/null 2>&1; then
  python3 -m build --wheel --no-isolation --outdir "${dist_dir}"
elif python3 setup.py --version >/dev/null 2>&1; then
  python3 setup.py bdist_wheel --dist-dir "${dist_dir}"
else
  echo "Missing build tooling. Run: pip install build wheel"
  exit 1
fi

echo "------------------------------------------------"
echo "✅ Success! Wheel created in ${dist_dir}"
echo "Run: pip install ${dist_dir}/*.whl"