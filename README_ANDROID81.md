# Twoyi with Android 8.1 (experimental)

This branch repackages the public Twoyi iOS IPA with the **Android 8.1 rootfs**
from the last open-source Twoyi release (APK `0.5.4`, `assets/rootfs.7z`). The
result is an **unsigned** IPA.

## Build

`Actions → Build unsigned Twoyi IPA (Android 8.1) → Run workflow`, then download
the `twoyi-android8.1-unsigned` artifact. Sideload with TrollStore / SideStore /
AltStore or your own certificate.

The workflow downloads the stock `twoyi_1.2.5_939.ipa`, replaces
`rom/system.erofs` with an EROFS image built from the 8.1 rootfs, rewrites the
rootfs manifest and lock files, disables AOT, drops `_CodeSignature`, and
produces a new IPA.

## Why AOT is disabled

The stock IPA contains ~2,860 AOT units translated from Android 13 code plus a
61 MB `__neo_aot` metadata section. Those units do not describe an 8.1 rootfs,
so the runtime is switched to the built-in `step` engine (`aot: false`,
`default_aot: false`). Expect slow boot: this path interprets guest code
instead of running the pre-translated native blocks.

## Status

Static-only repack. The IPA is structurally valid but **has not been boot-tested
on an iPhone/iPad**; the private AOT translator and the original tree-hash
algorithm are not public, so the generated manifest digest is ours and must be
accepted by the runtime for boot to succeed. Use at your own risk.
