# Tool Registry

Verified locally through 2026-08-31. External source repositories and downloaded binaries are intentionally not vendored in the parent Git history unless noted.

| Tool | Purpose | Version | Source | Installed | Notes |
|---|---|---|---|---|---|
| 7-Zip | Archive handling | 26.02 x64 | https://www.7-zip.org/ | Yes | Pre-existing at `C:\Program Files\7-Zip` |
| Git | Version control | 2.55.0.windows.5 | https://git-scm.com/ | Yes | Command verified |
| GitHub Desktop | Git GUI | 3.6.4 | https://desktop.github.com/ | Yes | Pre-existing per-user install |
| PCSX2 | Behaviour/rendering reference | Executable 2.6.3.0 | https://pcsx2.net/ | Yes | Pre-existing at `C:\Program Files\PCSX2`; uninstall metadata still reports 2.4.0 |
| Visual Studio | Native IDE/toolchain | Community 2022 17.14.39 (`17.14.37614.0`) | https://visualstudio.microsoft.com/ | Yes | `C:\Program Files\Microsoft Visual Studio\2022\Community`; launchable and complete per vswhere |
| MSVC | C++ compiler | Toolset 14.44.35207; compiler 19.44.35228 | Visual Studio Installer | Yes | x64 C++20 smoke build passed |
| Windows SDK | Windows headers/libraries | 10.0.26100.0 | Visual Studio Installer | Yes | Selected by CMake smoke build; 10.0.28000.0 is also present locally |
| Python | Analysis scripting | 3.13.7 | https://www.python.org/ | Yes | pip 25.2 verified |
| CMake | Build configuration | 4.4.3 | https://cmake.org/ | Yes | Standalone install; command verified |
| Ghidra | Reverse engineering | 12.1.3 | https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_12.1.3_build | Yes | Official per-user install under `%LOCALAPPDATA%\Programs\Ghidra\ghidra_12.1.3_PUBLIC`; headless startup verified |
| Emotion Engine Reloaded | Ghidra R5900/PS2 language | Commit `ae013ee1475dc970db4fdeba3ec88def6b933d43`; language 1.4.0 | https://github.com/chaoticgd/ghidra-emotionengine-reloaded | Yes | Unmodified `main` checkout; built 2026-08-31 for Ghidra 12.1.3 with cached Gradle 8.14.3; `r5900:LE:32:default` headless import and LQ/SQ/MMI/COP2 decoding verified |
| Gradle | Ghidra extension build | 8.14.3 | https://gradle.org/ | Cached | Existing wrapper distribution used; no additional system installation required |
| Java/JDK | Ghidra runtime | Eclipse Temurin 21.0.12.1+1 LTS | https://adoptium.net/ | Yes | 64-bit JDK; system `JAVA_HOME` configured |
| Noesis | Asset inspection/conversion | 4.474 | https://www.richwhitehouse.com/index.php?content=inc_projects.php&showproject=91 | Yes | Official portable release under `%LOCALAPPDATA%\Programs\Noesis`; GUI startup verified |
| HxD | Hex editor | 2.5.0.0 | https://mh-nexus.de/en/hxd/ | Yes | Installed at `C:\Program Files\HxD` |
| PS2Recomp | Experimental PS2 static recompiler | Commit `14b1e5cb39b4af7e6fc12f9a29fdc751efde49d7` | https://github.com/ran-j/PS2Recomp | Yes | Branch `main`; cloned recursively 2026-08-28 into `recomp/ps2recomp`; upstream commit date 2026-08-18 |
| Spartan PAK tooling | PAK listing/extraction | QuickBMS 0.12.0; script 0.1.1 | https://mirror.aluigi.org/quickbms_list.php | Yes | Local under `tools/external/spartan-pak-tools`; PAK0/PAK1 reads supported; rebuild/reimport unverified; no game data tested |
| RenderDoc | Graphics capture/debugging | 1.45.0 | https://renderdoc.org/ | Yes | Optional; command reports build `2fc0bc04cb95499635f63986a55bc6f67849dd9f` |
| Blender | Model inspection/conversion | 5.2.1 LTS | https://www.blender.org/ | Yes | Optional |
| FFmpeg | Audio/video processing | 9.0.1 full build | https://ffmpeg.org/ | Yes | Optional; Gyan Windows build |
| ImageMagick | Image/texture conversion | 7.1.2-29 Q16-HDRI x64 | https://imagemagick.org/ | Yes | Optional |
