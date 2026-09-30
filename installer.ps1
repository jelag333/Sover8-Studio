# Installe (ou répare) le Studio Tesseract sur ce PC Windows 64 bits.
# Usage : clic droit > Exécuter avec PowerShell, ou :
#   powershell -ExecutionPolicy Bypass -File installer.ps1 [-SansWhisper] [-SansGPU]
# Sans droits administrateur. Idempotent : relançable à tout moment.
param([switch]$SansWhisper, [switch]$SansGPU)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = 'Tls12'
$Studio = $PSScriptRoot
$TsrctVersion = '0.2.0'
$TsrctSha256 = '35822d306209476d5c80ac3fafed6be6110afd70840f6c7179e5a35caf57b988'  # tesseract-0.2.0-windows-x86_64.zip
function Etape($m) { Write-Host "`n== $m" -ForegroundColor Cyan }
function RefreshPath { $env:Path = [Environment]::GetEnvironmentVariable('Path','User') + ';' + [Environment]::GetEnvironmentVariable('Path','Machine') }

Etape 'Vérification du système'
$arch = if ($env:PROCESSOR_ARCHITEW6432) { $env:PROCESSOR_ARCHITEW6432 } else { $env:PROCESSOR_ARCHITECTURE }
if ($arch -ne 'AMD64') { throw "Windows 64 bits (x64) requis, trouvé : $arch" }
Write-Host "Windows x64 OK — studio : $Studio"

Etape "CLI Tesseract $TsrctVersion"
$tsrct = Join-Path $env:LOCALAPPDATA 'Tesseract\bin\tsrct.cmd'
$have = if (Test-Path $tsrct) { (& $tsrct --version) 2>$null } else { '' }
if ($have -notmatch [regex]::Escape($TsrctVersion)) {
    $zipName = "tesseract-$TsrctVersion-windows-x86_64.zip"
    $dl = Join-Path $env:TEMP ("tsrct-" + [Guid]::NewGuid().ToString('N').Substring(0, 6))  # chemin court (limite de 260 caractères)
    New-Item -ItemType Directory $dl | Out-Null
    $base = "https://github.com/mirage-hq/tesseract/releases/download/v$TsrctVersion"
    Invoke-WebRequest -UseBasicParsing "$base/$zipName" -OutFile "$dl\$zipName"
    Invoke-WebRequest -UseBasicParsing "$base/$zipName.sha256" -OutFile "$dl\$zipName.sha256"
    $hash = (Get-FileHash "$dl\$zipName" -Algorithm SHA256).Hash.ToLower()
    $published = ((Get-Content "$dl\$zipName.sha256" -Raw).Trim() -split '\s+')[0].ToLower()
    if ($hash -ne $published -or $hash -ne $TsrctSha256) { throw "Somme de contrôle invalide pour $zipName ($hash)" }
    Write-Host "Somme de contrôle SHA-256 vérifiée"
    Expand-Archive "$dl\$zipName" "$dl\x"
    $inst = Get-ChildItem "$dl\x" -Recurse -Filter install.ps1 | Select-Object -First 1
    powershell -NoProfile -ExecutionPolicy Bypass -File $inst.FullName
    if ($LASTEXITCODE -ne 0) { throw "L'installation de Tesseract a échoué" }
    Remove-Item -Recurse -Force $dl
}
Write-Host (& $tsrct --version)

Etape 'Python 3'
RefreshPath
$py = Get-Command python -All -ErrorAction SilentlyContinue | Where-Object { $_.Source -notlike '*WindowsApps*' } | Select-Object -First 1
if (-not $py) {
    winget install --id Python.Python.3.12 -e --scope user --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
    RefreshPath
    $py = Get-Command python -All -ErrorAction SilentlyContinue | Where-Object { $_.Source -notlike '*WindowsApps*' } | Select-Object -First 1
    if (-not $py) { $py = Get-Item "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" }
}
$pyExe = if ($py.Source) { $py.Source } else { $py.FullName }
Write-Host (& $pyExe --version)

Etape 'FFmpeg'
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    winget install --id Gyan.FFmpeg -e --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
    RefreshPath
}
Write-Host ((ffmpeg -hide_banner -version | Select-Object -First 1))

Etape 'Environnement Python du studio'
$venv = Join-Path $Studio '.venv'
if (-not (Test-Path "$venv\Scripts\python.exe")) { & $pyExe -m venv $venv }
$vpy = "$venv\Scripts\python.exe"
& $vpy -m pip install --quiet --upgrade pip
& $vpy -m pip install --quiet numpy
if (-not $SansWhisper) {
    & $vpy -m pip install --quiet -r (Join-Path $Studio 'outils\requirements.txt')
    $nvidia = Get-CimInstance Win32_VideoController | Where-Object { $_.Name -match 'NVIDIA' }
    if ($nvidia -and -not $SansGPU) {
        Write-Host "Carte NVIDIA détectée ($($nvidia[0].Name)) : bibliothèques CUDA pour Whisper"
        & $vpy -m pip install --quiet nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"
    }
}

Etape 'Skills Claude'
$skills = Join-Path $env:USERPROFILE '.claude\skills'
New-Item -ItemType Directory -Force $skills | Out-Null
foreach ($s in Get-ChildItem (Join-Path $Studio 'vendor\skills') -Directory) {
    $dest = Join-Path $skills $s.Name
    if (-not (Test-Path $dest)) { Copy-Item -Recurse $s.FullName $dest; Write-Host "installé : $($s.Name)" } else { Write-Host "déjà présent : $($s.Name)" }
}
$mine = Join-Path $skills 'studio-tesseract'
New-Item -ItemType Directory -Force $mine | Out-Null
Copy-Item -Force (Join-Path $Studio 'skill\studio-tesseract\SKILL.md') $mine
[IO.File]::WriteAllText((Join-Path $mine 'studio-path.txt'), $Studio, [Text.UTF8Encoding]::new($false))
Write-Host "installé : studio-tesseract -> $Studio"

Etape 'Vérification finale'
& (Join-Path $Studio 'studio.cmd') page
& (Join-Path $Studio 'studio.cmd') verifier
Write-Host "`nStudio prêt. Ouvre catalogue.html ou demande à Claude de monter une vidéo." -ForegroundColor Green
