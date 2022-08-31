# Upstream has set compiler flags to treat build warnings as errors for GCC.
# This effectively renders GCC unusable and requires hipamd to be build with
# LLVM/Clang. For details, see:
#   https://github.com/ROCm-Developer-Tools/hipamd/commit/48296291c83b7eea606ade26a8ba85780838c730
#   https://docs.fedoraproject.org/en-US/packaging-guidelines/#_compiler_macros
%global toolchain clang

# With ROCm > 5.1 rpmbuild yields empty debuginfo files, thus disable for now.
# This is also in line with what Debian does at the moment. For details, see:
#   https://github.com/ROCm-Developer-Tools/hipamd/issues/17
#   https://github.com/ROCm-Developer-Tools/hipamd/issues/24
#   https://salsa.debian.org/rocm-team/rocm-hipamd/-/blob/82920bbb9bf0deef723cdc6aa305e8598c264f03/debian/rules#L43
#   https://fedoraproject.org/wiki/Packaging:Debuginfo
%global debug_package %{nil}

# Cmake macro is called within sourcedir but HIP assumes it's called from build
%define __cmake_in_source_build 1

%global rocm_release 5.2
%global rocm_patch 1
%global rocm_version %{rocm_release}.%{rocm_patch}


Name:           rocm-hip
Version:        %{rocm_version}
Release:        1%{?dist}
Summary:        ROCm HIP Runtime

Url:            https://github.com/ROCm-Developer-Tools/hipamd
License:        MIT
# AMD HIP implementation
Source0:        https://github.com/ROCm-Developer-Tools/hipamd/archive/refs/tags/rocm-%{version}.tar.gz#/hipamd-%{version}.tar.gz
# HIP header files (platform independent)
Source1:        https://github.com/ROCm-Developer-Tools/HIP/archive/refs/tags/rocm-%{version}.tar.gz#/HIP-%{version}.tar.gz
# Bundled ROCclr and ROCm-OpenCL-Runtime source code
Source2:        https://github.com/RadeonOpenCompute/ROCm-OpenCL-Runtime/archive/refs/tags/rocm-%{version}.tar.gz#/ROCm-OpenCL-Runtime-%{version}.tar.gz
Source3:        https://github.com/ROCm-Developer-Tools/ROCclr/archive/refs/tags/rocm-%{version}.tar.gz#/ROCclr-%{version}.tar.gz

# SWDEV-335902 - Fix HIP when Git info unavailable
Patch0:         https://github.com/ROCm-Developer-Tools/hipamd/commit/56b32604729cca08bdcf00c7a69da8a75cc95b8a.patch#/0000-SWDEV-335902-Fix_unavailable_git_info.patch
# SWDEV-334908 - Guard the __noinline__ macro as it is also supported as keyword by clang
Patch1:         https://github.com/ROCm-Developer-Tools/hipamd/commit/28009bc68faf2b4dd8fda91c99b0725e1b063a18.patch#/0001-SWDEV-334908-Guard_noinline_macro.patch
# SWDEV-336248 - Use public icd header
Patch2:         https://github.com/ROCm-Developer-Tools/hipamd/commit/e8a481c4201b692d9dce7d3fe73f7b0b61eb4809.patch#/0002-SWDEV-336248-Use_public_icd_header.patch
# SWDEV-335990 - Use GNUInstallDirs - part 1
Patch3:         https://github.com/ROCm-Developer-Tools/hipamd/commit/f892306e227983a7c1943992ba70bf4e4b189105.patch#/0003-SWDEV-335990-Use_GNUInstallDirs.patch
# SWDEV-335990 - Use GNUInstallDirs - part 2
Patch4:         https://github.com/ROCm-Developer-Tools/hipamd/commit/c92a12faf39210e24d329cc2c7e94dd124e69fed.patch#/0004-SWDEV-335990-Use_GNUInstallDirs.patch
# SWDEV-336248 - Don't exclude cl_egl.h from install
Patch200:       https://github.com/RadeonOpenCompute/ROCm-OpenCL-Runtime/commit/b98828a206fef952abe2f65c337dafe0316c9e9e.patch#/0200-SWDEV-336248-Don-t-exclude-cl_egl.h-from-install.patch

BuildRequires:  cmake
BuildRequires:  git
BuildRequires:  clang-devel
BuildRequires:  llvm-devel
BuildRequires:  libffi-devel
BuildRequires:  zlib-devel
BuildRequires:  pkgconfig(numa)
BuildRequires:  pkgconfig(opengl)
BuildRequires:  pkgconfig(ocl-icd)
BuildRequires:  perl
# NOTE: Add rocminfo only for local builds on systems with AMD GPUs. The build
#       fails on Fedora's build systems if this is included.
#BuildRequires:  rocminfo
BuildRequires:  rocm-device-libs
BuildRequires:  rocm-comgr-devel
BuildRequires:  rocm-runtime-devel

Requires:       comgr(rocm) = %{rocm_release}

#Only the following architectures are supported:
# The kernel support only exists for x86_64, aarch64, and ppc64le
# 32bit userspace is excluded based on current Fedora policies
#TODO: ppc64le doesn't build on EPEL8 due to type casting issue
%if 0%{?rhel} <= 8 && 0%{?rhel}
ExclusiveArch:  x86_64 aarch64
%else
ExclusiveArch:  x86_64 aarch64 ppc64le
%endif

%description
HIP is a C++ Runtime API and Kernel Language that allows developers to create
portable applications for AMD and NVIDIA GPUs from single source code.

%package devel
Summary:        ROCm HIP development package
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
The AMD ROCm HIP development package.

%package samples
Summary:        ROCm HIP samples
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description samples
The AMD ROCm HIP samples.

%prep
%autosetup -N -b 1 -n hipamd-rocm-%{version}
# hipamd - apply upstream patches
%autopatch -p1 -m 0 -M 99
# hipamd - fix install directory:
#          https://github.com/ROCm-Developer-Tools/hipamd/issues/43
sed 's/LIBRARY DESTINATION lib/LIBRARY DESTINATION \${CMAKE_INSTALL_LIBDIR}/g' \
    -i src/hiprtc/CMakeLists.txt

# hipamd - fix rpath issue:
#          https://github.com/ROCm-Developer-Tools/hipamd/issues/22
sed -e "/CMAKE_INSTALL_RPATH.*CMAKE_INSTALL_LIBDIR/d" \
    -e "/CMAKE_INSTALL_RPATH_USE_LINK_PATH.*TRUE/d" \
    -i CMakeLists.txt

# Unpack bundled sources manually
cd ..
gzip -dc %{SOURCE2} | tar -xof -
gzip -dc %{SOURCE3} | tar -xof -
cd -

# ROCm-OpenCL-Runtime - apply upstream patches
cd ../ROCm-OpenCL-Runtime-rocm-%{version}
%autopatch -p1 -m 200 -M 299
cd -

# ROCclr - Enable experimental pre vega platforms
sed -i 's/\(ROC_ENABLE_PRE_VEGA.*\)false/\1true/' \
    ../ROCclr-rocm-%{version}/utils/flags.hpp

# ROCm-OpenCL-Runtime - Clean up unused bundled code:
#   ROCm OpenCL only compiles agains the bundled opencl2.2 headers. Remove all
#   others.
cd ../ROCm-OpenCL-Runtime-rocm-%{version}
ls -d khronos/* | grep -v headers | xargs rm -r
ls -d khronos/headers/* | grep -v opencl2.2 | xargs rm -r
rm -r khronos/headers/opencl2.2/tests/
cd -

%build
# Set location of clang++ for hipconfig perl script run by cmake:
export HIP_CLANG_PATH=%{_bindir}
mkdir build
cd build
%cmake -S.. -B. \
    -DHIP_COMMON_DIR=$(realpath ../../HIP-rocm-%{version}) \
    -DAMD_OPENCL_PATH=$(realpath ../../ROCm-OpenCL-Runtime-rocm-%{version}) \
    -DROCCLR_PATH=$(realpath ../../ROCclr-rocm-%{version}) \
    -DROCM_PATH=%{_prefix} \
    -DHIP_PLATFORM=amd \
    -DFILE_REORG_BACKWARD_COMPATIBILITY=OFF \
    -DCMAKE_INSTALL_LIBDIR=%{_lib} \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo
%cmake_build

%install
cd build
%cmake_install

%files
%doc README.md
%license LICENSE.txt
# This is not needed, and debian excludes it too:
%exclude %{_libdir}/.hipInfo
%{_libdir}/libamdhip64.so.5{,.*}
%{_libdir}/libhiprtc.so.5{,.*}
%{_libdir}/libhiprtc-builtins.so.5{,.*}
# Duplicated files:
%exclude %{_docdir}/*/LICENSE*

%files devel
%{_bindir}/*
# FIXME: hipVersion shouldn't be hidden, nor in bindir:
%{_bindir}/.hipVersion
%{_includedir}/hip
%{_libdir}/libamdhip64.so
%{_libdir}/libhiprtc.so
%{_libdir}/libhiprtc-builtins.so
%{_libdir}/cmake/hip
%{_libdir}/cmake/hip-lang

%files samples
%{_datadir}/hip/samples

%changelog
* Sun Aug 21 2022 Armin Wehrfritz <dkxls23 at gmail dot com> - 5.2.1-1
- Initial package for version 5.2.1
- Package based on spec files from mystro256/rocm-hip and Fedora's rocm-opencl
