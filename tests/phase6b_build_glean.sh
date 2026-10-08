#!/usr/bin/env bash
# Experimental container-side build. Invoke only in the pinned disposable
# Ubuntu container with the documented /work mount, not as a host installer.
set -euo pipefail
test -d /work/Glean/.git
export DEBIAN_FRONTEND=noninteractive
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
mkdir -p /etc/ssl/certs
if test -f /work/bootstrap-ca.crt; then
    cp /work/bootstrap-ca.crt /etc/ssl/certs/ca-certificates.crt
fi
sed -i 's|http://|https://|g' /etc/apt/sources.list.d/ubuntu.sources
apt-get update
apt-get install -y --no-install-recommends ghc cabal-install git curl ca-certificates python3 wget build-essential cmake ninja-build bison flex rsync m4 pkg-config binutils-dev libboost-all-dev libdouble-conversion-dev libdwarf-dev libevent-dev libfast-float-dev libfftw3-dev libfmt-dev libgflags-dev libgmock-dev libgoogle-glog-dev libgtest-dev libiberty-dev libjemalloc-dev liblz4-dev liblzma-dev libpcre3-dev librocksdb-dev libsnappy-dev libsodium-dev libssl-dev libtinfo-dev libunwind-dev libxxhash-dev libzstd-dev zlib1g-dev libnuma-dev libgmp-dev libaio-dev libbz2-dev squashfs-tools clang-15 libclang-15-dev libclang-cpp15-dev llvm-15-dev libre2-dev
echo '12d018bdd07efed470f278f22d94b33655c4fcbc44d28d97b5ebb7944d5607c5  /work/cabal-3.10.3.0.tar.xz' | sha256sum -c -
tar -xJf /work/cabal-3.10.3.0.tar.xz -C /usr/local/bin cabal
cd /work/Glean
git config --global --add safe.directory /work/Glean
git config --global --add safe.directory /work/Glean/hsthrift
test "$(git rev-parse HEAD)" = 4e576957778b721f28cec21556066a02c3ed84d0
test "$(git -C hsthrift rev-parse HEAD)" = e3c575885f9eda98e3c3aa9a1edd5011b6b14373
make glean.cabal
export INSTALL_PREFIX=/work/hsthrift-installed
./install_deps.sh --threads 1 --use-system-libs
export LD_LIBRARY_PATH=/work/hsthrift-installed/lib:/work/hsthrift-installed/lib64
export PKG_CONFIG_PATH=/work/hsthrift-installed/lib/pkgconfig:/work/hsthrift-installed/lib64/pkgconfig
export PATH=/work/hsthrift-installed/bin:$PATH
sed -i 's|url: http://hackage.haskell.org/|url: https://hackage.haskell.org/|' /root/.cabal/config
if ! test -f /root/.cabal/packages/hackage.haskell.org/01-index.tar; then cabal update; fi
cd hsthrift
make setup-folly
make setup-folly-version
cd ..
cat > cabal.project.local <<'EOF'
package glean-clang
    ghc-options: -pgmcxx /usr/bin/clang++-15 -optcxx-O0 -optcxx-g0 -optcxx-fno-addrsig
EOF
make MODE=dev CXX_MODE=cabal CABAL_CONFIG_FLAGS='--builddir=/work/Glean/.build/dev/dist-newbuild -f-bundled-folly -f-hack-tests -j1' EXTRA_GHC_OPTS='-O0 -optl-Wl,--no-as-needed -optl-lboost_context -optl/work/hsthrift-installed/lib/libfmt.so' -j1
mkdir -p glean/schema/cpp
cp .build/dev/codegen/gen-schema/glean/lang/clang/schema.h glean/schema/cpp/schema.h
# End Cabal's package-planning process before the large C++ compile: its
# retained heap otherwise competes with Clang under the 3 GiB container limit.
cabal --ghc-options='-O0 -optl-Wl,--no-as-needed -optl-lboost_context -optl/work/hsthrift-installed/lib/libfmt.so' --builddir=/work/Glean/.build/dev/dist-newbuild -f-bundled-folly -f-hack-tests -j1 build --only-configure glean-clang
clang_build=/work/Glean/.build/dev/dist-newbuild/build/x86_64-linux/ghc-9.4.7/glean-clang-0.1.0.0
cd glean/lang/clang
"$clang_build/setup/setup" build --builddir="$clang_build" exe:clang-index exe:clang-derive
cd /work/Glean
ghc --version
cabal --version
clang-15 --version
llvm-config-15 --version
dpkg-query -W > /work/packages.txt
touch /work/BUILD_SUCCESS
exec sleep infinity
