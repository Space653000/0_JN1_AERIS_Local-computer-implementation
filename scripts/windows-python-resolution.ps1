Set-StrictMode -Version Latest

function Test-AerisPythonExecutable {
  param([Parameter(Mandatory=$true)][string]$Executable)
  try {
    $output = @(& $Executable -c "import sys; print(sys.executable); raise SystemExit(0 if sys.version_info >= (3,10) else 9)" 2>$null)
    if ($LASTEXITCODE -ne 0) { return $null }
    $resolved = ($output | Where-Object { $_ -and $_.ToString().Trim() } | Select-Object -Last 1)
    if (-not $resolved) { return $null }
    $resolved = $resolved.ToString().Trim()
    if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) { return $null }
    return (Resolve-Path -LiteralPath $resolved).Path
  } catch {
    return $null
  }
}

function Resolve-AerisPythonFromLauncher {
  param([Parameter(Mandatory=$true)][string]$Selector)
  $launcher = Get-Command py -ErrorAction SilentlyContinue
  if (-not $launcher) { return $null }
  try {
    $output = @(& $launcher.Source $Selector -c "import sys; print(sys.executable); raise SystemExit(0 if sys.version_info >= (3,10) else 9)" 2>$null)
    if ($LASTEXITCODE -ne 0) { return $null }
    $candidate = ($output | Where-Object { $_ -and $_.ToString().Trim() } | Select-Object -Last 1)
    if (-not $candidate) { return $null }
    return (Test-AerisPythonExecutable -Executable $candidate.ToString().Trim())
  } catch {
    return $null
  }
}

function Get-AerisRegistryPythonCandidates {
  $roots = @(
    'HKCU:\Software\Python\PythonCore',
    'HKLM:\Software\Python\PythonCore',
    'HKLM:\Software\WOW6432Node\Python\PythonCore'
  )
  $items = New-Object System.Collections.Generic.List[string]
  foreach ($root in $roots) {
    if (-not (Test-Path $root)) { continue }
    foreach ($version in @(Get-ChildItem $root -ErrorAction SilentlyContinue)) {
      $installPath = Join-Path $version.PSPath 'InstallPath'
      try {
        $dir = (Get-ItemProperty -Path $installPath -ErrorAction Stop).'(default)'
        if (-not $dir) { $dir = (Get-Item -Path $installPath -ErrorAction Stop).GetValue('') }
        if ($dir) { $items.Add((Join-Path $dir 'python.exe')) }
      } catch {}
    }
  }
  return $items
}

function Resolve-AerisPython {
  # Prefer the Windows Python Launcher because WindowsApps aliases can exist while being non-executable.
  foreach ($selector in @('-3.11','-3')) {
    $resolved = Resolve-AerisPythonFromLauncher -Selector $selector
    if ($resolved) { return $resolved }
  }

  $common = New-Object System.Collections.Generic.List[string]
  foreach ($version in @('311','312','313','310')) {
    if ($env:LOCALAPPDATA) { $common.Add((Join-Path $env:LOCALAPPDATA "Programs\Python\Python$version\python.exe")) }
    if ($env:ProgramFiles) {
      $common.Add((Join-Path $env:ProgramFiles "Python$version\python.exe"))
      $common.Add((Join-Path $env:ProgramFiles "Python\Python$version\python.exe"))
    }
    $pf86 = ${env:ProgramFiles(x86)}
    if ($pf86) {
      $common.Add((Join-Path $pf86 "Python$version\python.exe"))
      $common.Add((Join-Path $pf86 "Python\Python$version\python.exe"))
    }
  }

  foreach ($candidate in @($common) + @(Get-AerisRegistryPythonCandidates)) {
    if (-not $candidate -or -not (Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }
    $resolved = Test-AerisPythonExecutable -Executable $candidate
    if ($resolved) { return $resolved }
  }

  # Generic `python` is deliberately late: Windows Store aliases may resolve but exit 9009.
  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) {
    $resolved = Test-AerisPythonExecutable -Executable $python.Source
    if ($resolved) { return $resolved }
  }

  if ($env:LOCALAPPDATA) {
    $base = Join-Path $env:LOCALAPPDATA 'Programs\Python'
    if (Test-Path $base) {
      foreach ($found in @(Get-ChildItem $base -Filter python.exe -Recurse -File -ErrorAction SilentlyContinue | Sort-Object FullName)) {
        $resolved = Test-AerisPythonExecutable -Executable $found.FullName
        if ($resolved) { return $resolved }
      }
    }
  }
  return $null
}

function Assert-AerisPythonVersion {
  param([Parameter(Mandatory=$true)][string]$Executable)
  $resolved = Test-AerisPythonExecutable -Executable $Executable
  if (-not $resolved) { throw 'AERIS requires an executable Python 3.10 or newer interpreter.' }
  return $resolved
}
