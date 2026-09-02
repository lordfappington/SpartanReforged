[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$python = (Get-Command python -ErrorAction Stop).Source
$venvRoot = Join-Path $repoRoot 'temp\menu-harness-venv'
$venvPython = Join-Path $venvRoot 'Scripts\python.exe'
$requirements = Join-Path $repoRoot 'tools\reforged\frontend\menu_harness_requirements.txt'
$entryPoint = Join-Path $repoRoot 'tools\reforged\frontend\menu_harness.py'
$modulePath = Join-Path $repoRoot 'tools\reforged\frontend'
$assetPath = Join-Path $repoRoot 'assets\reforged\frontend\main-menu'
$distRoot = Join-Path $repoRoot 'build\menu-harness'
$workRoot = Join-Path $repoRoot 'temp\menu-harness-pyinstaller'
$specRoot = Join-Path $repoRoot 'temp\menu-harness-spec'

if (-not (Test-Path -LiteralPath $venvPython)) {
    & $python -m venv $venvRoot
}
& $venvPython -m pip install --disable-pip-version-check --quiet -r $requirements

foreach ($target in @($distRoot, $workRoot, $specRoot)) {
    $full = [System.IO.Path]::GetFullPath($target)
    if (-not $full.StartsWith($repoRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to clean a path outside the repository: $full"
    }
    if (Test-Path -LiteralPath $full) {
        Remove-Item -LiteralPath $full -Recurse -Force
    }
}

New-Item -ItemType Directory -Force -Path $distRoot, $workRoot, $specRoot | Out-Null
& $venvPython -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --windowed `
    --name 'SpartanReforged-Menu' `
    --contents-directory 'runtime' `
    --distpath $distRoot `
    --workpath $workRoot `
    --specpath $specRoot `
    --paths $modulePath `
    --add-data "${assetPath};assets/reforged/frontend/main-menu" `
    $entryPoint
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

$executable = Join-Path $distRoot 'SpartanReforged-Menu\SpartanReforged-Menu.exe'
if (-not (Test-Path -LiteralPath $executable)) {
    throw "Build completed without the expected executable: $executable"
}
Write-Output "Menu harness ready: $executable"
