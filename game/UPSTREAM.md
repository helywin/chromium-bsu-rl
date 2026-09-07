# Upstream provenance

- Release: Chromium B.S.U. 0.9.16.1.
- Source: https://downloads.sourceforge.net/project/chromium-bsu/Chromium%20B.S.U.%20source%20code/chromium-bsu-0.9.16.1.tar.gz
- Archive SHA512: `1d202c0704e16b31d93c552ae6cfc17caf1182a9ec80730a981cd99c8ca8cb64d4e6e838691aa86e17ea23b7c2c0b1e7b1f4dab91bbc6129f9bf86801f2b27c8`.
- Imported 2026-09-07 in commit `f6a2b53`: complete release tree, without the enclosing archive directory; no binaries generated locally.
- Preserve COPYING, AUTHORS, README and data/wav/license.txt. Upstream README identifies game license as Clarified Artistic and sounds as MIT/Expat.

## Distribution fixes

Both patches in `patches/` came from https://gitlab.archlinux.org/archlinux/packaging/packages/chromium-bsu/-/tree/main and are already applied to this tree. Do not apply again at build time.

| Patch | SHA512 |
|---|---|
| use_fabs_for_floats.patch | `78b0de083c1c11e56aa0e864900c0c2c163f9828505402e63d5eba6092cb2ce2449747c7d5dbd40b96e801f872795a57dc5f247818f4e3d142a3f3af0d4d188d` |
| ax_check_gl_m4.patch | `5878c439e2d193d15774ab4e976a7da59696fefd79e4f6c382f3ccb9f6ab1ffe2d9ae50801a3fbfb08097e6f25ac99eb4e67c126d84b998474f5fe2dc594d2da` |

The examined Arch 0.9.16.1-4 PKGBUILD SHA256 was `5d6d67aa494385653f5ab66e2d3f67aab25cbb01dc3b43f4bbc08de1d7a436b3`.
Compare with the pristine import commit to reproduce local changes. Autotools output is regenerated only in ignored build copies.
