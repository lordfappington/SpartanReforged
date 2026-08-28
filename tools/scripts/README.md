# Internal Analysis Scripts

All scripts use only the Python standard library. Source inputs are opened read-only; report files are written only to the output paths you specify (or the current directory defaults).

## `inventory.py`

Creates deterministic CSV and JSON file inventories with relative paths, names, extensions, byte sizes, and SHA-256 hashes.

```powershell
python .\tools\scripts\inventory.py C:\path\to\copy --csv .\logs\extraction\inventory.csv --json .\logs\extraction\inventory.json
```

## `find_magic.py`

Displays a hexadecimal and ASCII view of the first bytes of one file or every file in a directory tree. The default is 64 bytes.

```powershell
python .\tools\scripts\find_magic.py C:\path\to\unknown --bytes 128
```

## `hash_compare.py`

Compares two directory trees by relative path and SHA-256, reporting identical, changed, and one-sided files.

```powershell
python .\tools\scripts\hash_compare.py C:\path\to\version-a C:\path\to\version-b
```

## `extension_report.py`

Groups files by case-normalized extension and writes counts, aggregate sizes, extrema, and deterministic example paths to CSV and JSON.

```powershell
python .\tools\scripts\extension_report.py C:\path\to\copy --csv .\logs\analysis\extensions.csv --json .\logs\analysis\extensions.json
```

Use `python <script> --help` for all options. Do not point these tools at original media when a verified working copy is available instead.
