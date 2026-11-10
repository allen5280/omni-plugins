"""Link-delivery build: 4 chunks (<=135 MB) + one installer zip. The .bat finds pieces by size+SHA-256, whatever their file names."""
import base64, os, textwrap, hashlib, zipfile, shutil
NAME='happy4_v4_master'; MASTER='happy4_v4_master.mp4'; D=f'_jy4/{NAME}'; OUT=os.environ.get('OUT_DIR','deliver')
shutil.rmtree(OUT,ignore_errors=True); os.makedirs(OUT)
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<22),b''): h.update(b)
    return h.hexdigest()
SIZE=os.path.getsize(MASTER); SHA=sha(MASTER)
def split(n_or_chunk, prefix, by_count=False):
    out=[]; 
    with open(MASTER,'rb') as f:
        i=0
        csize = -(-SIZE//n_or_chunk) if by_count else n_or_chunk
        while True:
            b=f.read(csize)
            if not b: break
            i+=1; fn=f'{OUT}/{prefix}{i}.zip'; open(fn,'wb').write(b); out.append((fn,len(b),hashlib.sha256(b).hexdigest()))
    return out
B=split(135*1024*1024,'video_part')           # link delivery
A=[]                                           # the two app-card parts, so either set works
with open(MASTER,'rb') as f:
    half=-(-SIZE//2)
    for i in range(2):
        b=f.read(half); A.append((None,len(b),hashlib.sha256(b).hexdigest()))
def ps_scheme(s): return '@(' + ','.join("@{n=[long]%d;s='%s'}"%(n,h) for _,n,h in s) + ')'
def b64(fn): return '\n'.join(textwrap.wrap(base64.b64encode(open(f'{D}/{fn}','rb').read()).decode(),120))
ps=r'''#PSSTART
$ErrorActionPreference = 'Stop'
$here = $env:HERE.TrimEnd('\')
$name = '__NAME__'
$expect = '__SHA__'
$size = [long]__SIZE__
$schemes = @(__SB__, __SA__)
function FileSha($p) { (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLower() }
Write-Host '== happy4 v4 : full-quality master -> JianYing draft =='
$vid = [Environment]::GetFolderPath('MyVideos')
if (-not $vid) { $vid = $here }
$work = Join-Path $vid 'happy4_v4'
New-Item -ItemType Directory -Force -Path $work | Out-Null
$master = Join-Path $work 'happy4_v4_master.mp4'
$ok = $false
if (Test-Path -LiteralPath $master) {
  if ((Get-Item -LiteralPath $master).Length -eq $size) { if ((FileSha $master) -eq $expect) { $ok = $true } }
}
if (-not $ok) {
  $dirs = @($here)
  try { $dl = (New-Object -ComObject Shell.Application).NameSpace('shell:Downloads').Self.Path; if ($dl) { $dirs += $dl } } catch {}
  $dirs += [Environment]::GetFolderPath('Desktop')
  $dirs = @($dirs | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique)
  $sizes = @(); foreach ($sc in $schemes) { foreach ($p in $sc) { $sizes += $p.n } }
  Write-Host 'Looking for the downloaded video parts in:'; $dirs | ForEach-Object { Write-Host "  $_" }
  $map = @{}
  foreach ($d in $dirs) {
    foreach ($f in @(Get-ChildItem -LiteralPath $d -File | Where-Object { $sizes -contains $_.Length })) {
      $h = FileSha $f.FullName
      if (-not $map.ContainsKey($h)) { $map[$h] = $f.FullName }
    }
  }
  $use = $null; $best = 0; $need = 0
  foreach ($sc in $schemes) {
    $n = 0; foreach ($p in $sc) { if ($map.ContainsKey($p.s)) { $n++ } }
    if (($n -eq $sc.Count) -and (-not $use)) { $use = $sc }
    if ($n -ge $best) { $best = $n; $need = $sc.Count }
  }
  if (-not $use) {
    Write-Host "ERROR: found $best of the video parts, but all are needed. Download every video link (wait until each download finishes), then run this again." -ForegroundColor Red
    exit 1
  }
  Write-Host "Joining $($use.Count) parts (bit-exact copy, no re-encode) ..."
  $out = [IO.File]::Create($master)
  foreach ($p in $use) { $in = [IO.File]::OpenRead($map[$p.s]); $in.CopyTo($out); $in.Close() }
  $out.Close()
  Write-Host 'Verifying SHA-256 ...'
  if ((FileSha $master) -ne $expect) {
    Remove-Item -LiteralPath $master
    Write-Host 'ERROR: checksum mismatch after joining. Download the video parts again and re-run.' -ForegroundColor Red
    exit 1
  }
}
Write-Host "OK: master is bit-identical to the original -> $master" -ForegroundColor Green
$cands = @(
  (Join-Path $env:LOCALAPPDATA 'JianyingPro\User Data\Projects\com.lveditor.draft'),
  (Join-Path $env:LOCALAPPDATA 'CapCut\User Data\Projects\com.lveditor.draft')
)
$root = $cands | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $root) {
  Write-Host 'JianYing draft folder was not found automatically. The video file is ready - you can simply drag it into JianYing:' -ForegroundColor Yellow
  Write-Host "  $master"
  $root = Read-Host 'Or paste the full path of the folder that holds your JianYing drafts (Enter to skip)'
}
if (-not $root) { Start-Process explorer.exe $work; exit 0 }
$root = $root.Trim('"')
if (-not (Test-Path -LiteralPath $root)) { Write-Host "ERROR: folder does not exist: $root" -ForegroundColor Red; exit 1 }
$dst = Join-Path $root $name
if (Test-Path -LiteralPath $dst) {
  $bak = $dst + '_old_' + (Get-Date -Format 'yyyyMMdd_HHmmss')
  Rename-Item -LiteralPath $dst -NewName (Split-Path -Leaf $bak)
  Write-Host "An older draft with the same name was kept as: $bak"
}
New-Item -ItemType Directory -Force -Path $dst | Out-Null
$run = $work -replace '\\', '/'
$enc = New-Object System.Text.UTF8Encoding($false)
$files = @{}
$files['draft_content.json'] = @'
__CONTENT__
'@
$files['draft_meta_info.json'] = @'
__META__
'@
foreach ($k in $files.Keys) {
  $raw = [Convert]::FromBase64String(($files[$k] -replace '\s', ''))
  $t = $enc.GetString($raw).Replace('##RUNDIR##', $run)
  [IO.File]::WriteAllText((Join-Path $dst $k), $t, $enc)
}
Write-Host "Done. Open JianYing - the draft '$name' is in your draft list." -ForegroundColor Green
Write-Host "The draft uses this file, keep it there: $master"
Write-Host 'The downloaded parts are no longer needed and can be deleted.'
Start-Process explorer.exe $work
'''.replace('__NAME__',NAME).replace('__SHA__',SHA).replace('__SIZE__',str(SIZE)).replace('__SB__',ps_scheme(B)).replace('__SA__',ps_scheme(A)).replace('__CONTENT__',b64('draft_content.json')).replace('__META__',b64('draft_meta_info.json'))
head='''@echo off
setlocal
set "HERE=%~dp0"
set "SELF=%~f0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=[IO.File]::ReadAllText($env:SELF); iex $s.Substring($s.IndexOf('#PS'+'START'))"
echo.
pause
exit /b
'''
txt=(head+ps).replace('\r\n','\n').replace('\n','\r\n'); assert all(ord(c)<128 for c in txt)
readme=('happy4 v4 - full-quality master for JianYing\r\n\r\n1. Download all the video links (4 files). Leave them in your Downloads folder. Do not open them.\r\n'
 '2. Double-click install_v4.bat (this file can be run from anywhere).\r\n3. Open JianYing: the draft "happy4_v4_master" is in the list.\r\n\r\n'
 'The joined video is saved to your Videos\\happy4_v4 folder. If the installer cannot find JianYing, just drag that video into JianYing.\r\n')
with zipfile.ZipFile(f'{OUT}/installer.zip','w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('install_v4.bat',txt); z.writestr('README_v4.txt',readme)
open(f'{OUT}/install_v4.bat','w',newline='').write(txt)
print('master',SIZE,SHA[:16]); [print(os.path.basename(f),n,h[:12]) for f,n,h in B]; print('installer.zip',os.path.getsize(f'{OUT}/installer.zip'))
