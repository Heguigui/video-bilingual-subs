param(
    [string]$Playlist,      # 本地 m3u8 文件
    [string]$PlaylistFile,  # 或者: 纯 URL 清单, 每行一条
    [Parameter(Mandatory = $true)][string]$OutDir,
    [string]$Ext = 'ts',
    [int]$Workers = 10
)

$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

if ($PlaylistFile) {
    $urls = @(Get-Content $PlaylistFile | Where-Object { $_ -match '^https?://' })
} elseif ($Playlist) {
    $urls = @(Get-Content $Playlist | Where-Object { $_ -match '^https?://' })
} else {
    throw 'need -Playlist or -PlaylistFile'
}

$total = $urls.Count
Write-Output "total $total"

$chunks = @()
for ($w = 0; $w -lt $Workers; $w++) {
    $part = @()
    for ($k = $w; $k -lt $total; $k += $Workers) { $part += , @($k, $urls[$k]) }
    $chunks += , $part
}

$jobs = @()
foreach ($part in $chunks) {
    $jobs += Start-Job -ScriptBlock {
        param($part, $dir, $ext)
        foreach ($item in $part) {
            $idx = $item[0]; $u = $item[1]
            $out = Join-Path $dir ('{0:d4}.{1}' -f $idx, $ext)
            if ((Test-Path $out) -and (Get-Item $out).Length -gt 400) { continue }
            for ($try = 0; $try -lt 6; $try++) {
                try {
                    Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 120 -OutFile $out
                    if ((Get-Item $out).Length -gt 400) { break }
                } catch {
                    Start-Sleep -Seconds 2
                }
            }
        }
    } -ArgumentList $part, $OutDir, $Ext
}

$jobs | Wait-Job | Out-Null
$jobs | Remove-Job
$done = (Get-ChildItem $OutDir -Filter "*.$Ext" | Measure-Object).Count
Write-Output "done $done / $total"
if ($done -lt $total) { Write-Output 'MISSING SEGMENTS - rerun to fill gaps' }
