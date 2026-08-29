# PS2 Disc Identity

Identification performed read-only on 2026-08-29. No filesystem extraction, archive unpacking, executable copying, or image modification was performed.

## Image Fingerprint

| Field | Value |
|---|---|
| Filename | `Spartan - Total Warrior (Europe, Australia) (En,Fr,De,Es,It).iso` |
| Size | 2,199,420,928 bytes |
| SHA-256 | `7d7092a4d379cbd83da3ad1ede6ebd88db031c6c774039f39cf6c8f4af00dbf6` |
| MD5 | `491931ef831f87bb22cceef3aca14871` |
| ISO9660 system identifier | `PLAYSTATION` |
| ISO9660 volume label | Empty / not set |
| Logical block size | 2,048 bytes |
| Declared sectors | 1,073,936 |
| Declared volume size | 2,199,420,928 bytes |

## Release Identity

### Confirmed

- Game: *Spartan: Total Warrior* for PlayStation 2.
- Serial/product code: `SLES-53393` (`SLES_533.93` as the ISO boot filename).
- Region family: Europe/Australia.
- Video mode: PAL, explicitly declared by `SYSTEM.CNF`.
- Disc version: 1.01, explicitly declared by `SYSTEM.CNF`.
- Edition/build: original multilingual Europe/Australia build (English, French, German, Spanish, Italian).
- The filename, byte size, MD5, serial, version, and language set match the verified [Redump record 7850](https://redump.info/disc/7850). Redump records the same disc data for the European `SLES-53393` and Australian `SLES-53393-ANZ` packaging variants.

### Likely

- The executable build date is 2005-08-16. This is reported by Redump and is consistent with the ISO directory timestamp for the boot executable.
- The ISO mastering/filesystem creation date is 2005-08-18 11:28:36 at UTC+09:00, as recorded in the Redump PVD metadata.

### Unknown

- Whether the source physical disc used European or Australian packaging. Both packaging variants map to the same verified disc image and internal serial.
- No separate internal source-control build identifier was observed in the permitted metadata.

## Boot Configuration

`SYSTEM.CNF` is 56 bytes and contains:

```text
BOOT2 = cdrom0:\SLES_533.93;1
VER = 1.01
VMODE = PAL
```

Main executable: `SLES_533.93` (3,656,280 bytes).

Minimal header inspection confirms a little-endian MIPS ELF32 executable (`ET_EXEC`, machine value 8) with entry point `0x00200008` and ELF flags `0x20924000`. No executable content was copied from the image.

## Shallow ISO Root Inventory

The `.` and `..` ISO directory records are omitted from this human-readable inventory.

| Root name | Type | ISO record size |
|---|---|---:|
| `SYSTEM.CNF` | File | 56 bytes |
| `SLES_533.93` | File | 3,656,280 bytes |
| `GENERAL.PAK` | File | 29,074 bytes |
| `E_DATA.PAK` | File | 1,514,409,600 bytes |
| `IOP` | Directory | 810 bytes |
| `DATA` | Directory | 1,716 bytes |

No directory was traversed and neither PAK archive was opened.

## Structural Health

The image appears healthy and is an exact match for the referenced verified Redump dump:

- Valid ISO9660 primary volume descriptor (`CD001`, version 1).
- Valid volume descriptor terminator.
- Declared volume byte count exactly equals the image file size.
- Root directory records parse consistently within their declared extent.
- `SYSTEM.CNF` resolves to a root-level executable.
- Boot executable begins with a valid PS2-compatible MIPS ELF32 header.
- Filename, size, and MD5 exactly match the verified public disc record.

This is a structural and checksum identity result, not an exhaustive sector-by-sector optical-disc error analysis.

