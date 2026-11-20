param([string]$Version = "3.13.5", [switch]$UseLocalPackages)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$buildRoot = Join-Path $projectRoot "portable-build"
$packageRoot = Join-Path $projectRoot "dist\MeetingInterpreter"
$runtime = Join-Path $packageRoot "runtime"
$zipPath = Join-Path $buildRoot "python-embed.zip"
$python = Join-Path $runtime "python.exe"
$versionParts = $Version.Split(".")
$pythonShortVersion = $versionParts[0] + $versionParts[1]

New-Item -ItemType Directory -Force -Path $buildRoot, $packageRoot, $runtime | Out-Null
if (-not (Test-Path -LiteralPath $zipPath)) {
    $url = "https://www.python.org/ftp/python/$Version/python-$Version-embed-amd64.zip"
    & curl.exe -L --fail --retry 3 --output $zipPath $url
    if ($LASTEXITCODE -ne 0) { throw "Python runtime download failed" }
}
Expand-Archive -LiteralPath $zipPath -DestinationPath $runtime -Force

$pth = Join-Path $runtime "python$pythonShortVersion._pth"
Set-Content -LiteralPath $pth -Value @("python$pythonShortVersion.zip", ".", "Lib\site-packages", "..\src", "import site") -Encoding ASCII

& $python -m pip --version 2>$null
if ($LASTEXITCODE -ne 0) {
    & curl.exe -L --fail --retry 3 --output (Join-Path $buildRoot "get-pip.py") "https://bootstrap.pypa.io/get-pip.py"
    & $python (Join-Path $buildRoot "get-pip.py") --no-cache-dir --no-warn-script-location
    if ($LASTEXITCODE -ne 0) { throw "pip installation failed" }
}
if ($UseLocalPackages) {
    $sitePackages = Join-Path $projectRoot ".venv\Lib\site-packages"
    Get-ChildItem -LiteralPath $sitePackages -Force | Where-Object {
        $_.Name -notmatch '^(pip|setuptools|pkg_resources|_distutils_hack|pytest|_pytest|psutil|__pycache__|_editable_impl_local_meeting_interpreter|local_meeting_interpreter-.*\.dist-info)'
    } | Copy-Item -Destination (Join-Path $runtime "Lib\site-packages") -Recurse -Force
} else {
    & $python -m pip install --no-cache-dir --index-url https://mirrors.aliyun.com/pypi/simple --no-warn-script-location -r (Join-Path $projectRoot "requirements-portable.txt")
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed" }
}

Copy-Item -LiteralPath (Join-Path $projectRoot "src") -Destination $packageRoot -Recurse -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "tools\portable_bootstrap.py") -Destination (Join-Path $runtime "portable_bootstrap.py") -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "THIRD-PARTY-NOTICES.txt") -Destination $packageRoot -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "models") -Destination $packageRoot -Recurse -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "assets") -Destination $packageRoot -Recurse -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "Interpreter.exe") -Destination $packageRoot -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "PORTABLE-README.txt") -Destination $packageRoot -Force

# The application is loaded from the adjacent src directory, never an editable install.
Get-ChildItem -LiteralPath (Join-Path $runtime "Lib\site-packages") -Force | Where-Object {
    $_.Name -match '^_editable_impl_local_meeting_interpreter|^local_meeting_interpreter-.*\.dist-info$'
} | Remove-Item -Recurse -Force

Get-ChildItem -LiteralPath $packageRoot -Directory -Filter "__pycache__" -Recurse | Remove-Item -Recurse -Force
Get-ChildItem -LiteralPath $runtime -Directory -Filter "PySide6_Addons*" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
& $python (Join-Path $projectRoot "tools\trim_portable.py") $packageRoot
$zipOutput = Join-Path $projectRoot "dist\MeetingInterpreter-windows-x64.zip"
if (Test-Path -LiteralPath $zipOutput) { Remove-Item -LiteralPath $zipOutput -Force }
Compress-Archive -LiteralPath $packageRoot -DestinationPath $zipOutput -CompressionLevel Optimal
Write-Output "Portable package: $packageRoot"
Write-Output "ZIP: $zipOutput"
