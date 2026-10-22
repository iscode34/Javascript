# capture_session.ps1 -- real desktop screenshots of the running programs.
param([string]$Only = 'all')       # all | net | tests | threaded
$ErrorActionPreference = 'Stop'
$root = 'F:\Nusa Putra\SM2\PARALLEL'
$shots = Join-Path $root 'shots'
New-Item -ItemType Directory -Force -Path $shots | Out-Null
Set-Location $root

Add-Type -AssemblyName System.Windows.Forms, System.Drawing
try { Add-Type -AssemblyName Microsoft.VisualBasic } catch { }
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr h, int x, int y, int w, int hh, bool repaint);
  [DllImport("user32.dll")] public static extern void keybd_event(byte code, byte scan, uint flags, UIntPtr extra);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint flags);
}
"@

function Get-BestWindow([string]$prefix) {
  # Several processes can carry the same title prefix; keep the biggest window.
  $best = $null; $bestArea = 0
  foreach ($p in (Get-Process | Where-Object { $_.MainWindowTitle -like "$prefix*" })) {
    if ($p.MainWindowHandle -eq 0) { continue }
    $r = New-Object Win32+RECT
    if ([Win32]::GetWindowRect($p.MainWindowHandle, [ref]$r)) {
      $area = ($r.Right - $r.Left) * ($r.Bottom - $r.Top)
      if ($area -gt $bestArea) { $bestArea = $area; $best = $p }
    }
  }
  return $best
}

function Find-Window([string]$prefix) {
  for ($i = 0; $i -lt 60; $i++) {
    $p = Get-BestWindow $prefix
    if ($p) { return $p }
    Start-Sleep -Milliseconds 250
  }
  throw "window not found: $prefix"
}

function Focus-Window([string]$prefix) {
  $p = Find-Window $prefix
  $h = $p.MainWindowHandle
  for ($try = 1; $try -le 8; $try++) {
    [Win32]::ShowWindow($h, 9) | Out-Null
    try { [Microsoft.VisualBasic.Interaction]::AppActivate($p.Id) | Out-Null } catch { }
    if ([Win32]::GetForegroundWindow() -ne $h) {
      [Win32]::keybd_event(0x12, 0, 0, [UIntPtr]::Zero)
      [Win32]::keybd_event(0x12, 0, 2, [UIntPtr]::Zero)
      [Win32]::SetForegroundWindow($h) | Out-Null
    }
    Start-Sleep -Milliseconds 350
    if ([Win32]::GetForegroundWindow() -eq $h) { return $p }
  }
  throw "cannot focus window: $prefix"
}

function Measure-Colors($bmp) {
  $seen = New-Object 'System.Collections.Generic.HashSet[int]'
  for ($x = 0; $x -lt $bmp.Width; $x += 17) {
    for ($y = 0; $y -lt $bmp.Height; $y += 17) { [void]$seen.Add($bmp.GetPixel($x, $y).ToArgb()) }
  }
  return $seen.Count
}

function Capture-Window([string]$prefix, [string]$out) {
  $p = Find-Window $prefix
  $h = $p.MainWindowHandle
  [Win32]::ShowWindow($h, 9) | Out-Null
  [Win32]::MoveWindow($h, 30, 30, 1200, 660, $true) | Out-Null
  Start-Sleep -Milliseconds 800
  $r = New-Object Win32+RECT
  [Win32]::GetWindowRect($h, [ref]$r) | Out-Null
  $w = $r.Right - $r.Left; $hh = $r.Bottom - $r.Top
  if ($w -lt 800 -or $hh -lt 300) { throw "window too small: $prefix ($w x $hh)" }

  # attempt A: PrintWindow (works even when another window is on top)
  $a = New-Object System.Drawing.Bitmap $w, $hh
  $ga = [System.Drawing.Graphics]::FromImage($a)
  $hdc = $ga.GetHdc()
  $okPrint = [Win32]::PrintWindow($h, $hdc, 2)
  $ga.ReleaseHdc($hdc); $ga.Dispose()
  $scoreA = if ($okPrint) { Measure-Colors $a } else { 0 }

  # attempt B: bring to front and grab the screen region
  $b = $null; $scoreB = 0
  try {
    $null = Focus-Window $prefix
    $r2 = New-Object Win32+RECT
    [Win32]::GetWindowRect($h, [ref]$r2) | Out-Null
    $w2 = $r2.Right - $r2.Left; $hh2 = $r2.Bottom - $r2.Top
    $b = New-Object System.Drawing.Bitmap $w2, $hh2
    $gb = [System.Drawing.Graphics]::FromImage($b)
    $gb.CopyFromScreen($r2.Left, $r2.Top, 0, 0, (New-Object System.Drawing.Size $w2, $hh2))
    $gb.Dispose()
    $scoreB = Measure-Colors $b
  } catch {
    Write-Host "  (screen grab failed: $($_.Exception.Message))"
  }

  if ($scoreB -gt $scoreA -and $b) { $final = $b; $score = $scoreB; $how = 'screen' }
  else { $final = $a; $score = $scoreA; $how = 'printwindow' }
  $final.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
  Write-Host ("captured {0} -> {1} ({2}x{3}, {4} distinct colours, via {5})" -f `
      $prefix, (Split-Path $out -Leaf), $final.Width, $final.Height, $score, $how)
  if ($a) { $a.Dispose() }
  if ($b) { $b.Dispose() }
  if ($score -lt 10) { throw "capture looks blank: $out" }
}

function Type-Into([string]$prefix, [string]$text) {
  $null = Focus-Window $prefix          # throws unless this window really has focus
  $ws = New-Object -ComObject WScript.Shell
  $ws.SendKeys($text)
}

function Start-Console([string]$title, [string]$command) {
  $inner = "mode con cols=116 lines=34 >nul & title $title & $command"
  return Start-Process conhost.exe -WorkingDirectory $root `
    -ArgumentList 'cmd.exe', '/k', $inner -PassThru
}

function Stop-Console($proc) {
  Get-CimInstance Win32_Process -Filter "ParentProcessId = $($proc.Id)" -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
  Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
}

function Cleanup-Stale {
  Get-Process | Where-Object { $_.MainWindowTitle -match '^(PROBE_|SOCKET |THREADED )' } |
    ForEach-Object {
      Write-Host "closing stale window: $($_.ProcessName) $($_.Id) [$($_.MainWindowTitle)]"
      Get-CimInstance Win32_Process -Filter "ParentProcessId = $($_.Id)" -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
      Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
  Start-Sleep -Milliseconds 900
}

Cleanup-Stale

# --- 1. server + client, real typing ------------------------------------
if ($Only -in @('all', 'net')) {
Write-Host "`n=== starting server window (port 5090) ==="
$srv = Start-Console 'SOCKET SERVER' 'python server.py --port 5090'
Start-Sleep -Seconds 3

Write-Host "=== starting client window (port 5090) ==="
$cli = Start-Console 'SOCKET CLIENT' 'python client.py --port 5090'
Start-Sleep -Seconds 3

Type-Into 'SOCKET CLIENT' 'Halo server, ini pesan pertama dari client.{ENTER}'
Start-Sleep -Milliseconds 1300
Type-Into 'SOCKET CLIENT' 'Pesan kedua: uji komunikasi dua arah.{ENTER}'
Start-Sleep -Milliseconds 1300
Type-Into 'SOCKET CLIENT' 'Pesan ketiga: terima kasih, server.{ENTER}'
Start-Sleep -Milliseconds 1500

Write-Host "=== capturing client window ==="
Capture-Window 'SOCKET CLIENT' (Join-Path $shots 'fig1_client.png')

Write-Host "=== capturing server window ==="
Capture-Window 'SOCKET SERVER' (Join-Path $shots 'fig2_server.png')

Stop-Console $cli
Stop-Console $srv
Start-Sleep -Seconds 1
}

# --- 2. automated test suite window -------------------------------------
if ($Only -in @('all', 'tests')) {
Write-Host "`n=== starting test-suite window ==="
$test = Start-Console 'SOCKET TESTS' 'python demo_test.py --brief'
Start-Sleep -Seconds 13
Capture-Window 'SOCKET TESTS' (Join-Path $shots 'fig3_tests.png')
Stop-Console $test
Start-Sleep -Seconds 1
}

# --- 3. threaded server, three simultaneous clients ---------------------
if ($Only -in @('all', 'threaded')) {
Write-Host "`n=== starting threaded server window (port 5091) ==="
$thr = Start-Console 'THREADED SERVER' 'python server_threaded.py --port 5091'
Start-Sleep -Seconds 3
& python (Join-Path $shots 'concurrent_clients.py') 5091
Start-Sleep -Milliseconds 900
Capture-Window 'THREADED SERVER' (Join-Path $shots 'fig4_threaded.png')
Stop-Console $thr
}

Write-Host "`n=== done ==="
Get-ChildItem $shots -Filter '*.png' | Select-Object Length, Name | Format-Table -AutoSize
