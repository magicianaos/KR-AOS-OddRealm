<#
  Odd Realm 한글패치 설치 스크립트

  실행 방법 : 이 파일을 우클릭 -> "PowerShell에서 실행"

  실행 파일(exe)이 아닌 순수 텍스트 스크립트입니다.
  메모장으로 열어 아래 내용을 전부 직접 확인할 수 있습니다.

  하는 일
    1. Odd Realm 설치 폴더를 찾는다
    2. 패치 대상 파일 5개를 SHA-256 으로 대조해 원본이 맞는지 확인한다
    3. 원본을 게임 폴더의 _KoreanPatch_Backup 안에 백업한다
    4. 같은 폴더의 patch.orkp 에 담긴 차분 데이터를 적용한다
    5. 결과를 SHA-256 으로 다시 검증한다

  하지 않는 일
    - 네트워크 통신을 하지 않는다 (다운로드/업로드 없음)
    - 게임 폴더 밖의 파일을 건드리지 않는다
    - 레지스트리는 Steam 설치 경로를 읽기만 한다 (쓰기 없음)
    - 다른 프로그램을 실행하지 않는다
#>

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
# DeflateStream 은 .NET Framework 기본 어셈블리에 있음. 혹시 없는 환경 대비.
try { Add-Type -AssemblyName System.IO.Compression -ErrorAction SilentlyContinue | Out-Null } catch {}

$AppName    = 'Odd Realm 한글패치'
$AppVersion = '1.0.3'
$BackupRoot = '_KoreanPatch_Backup'
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path

# ---------------- 공통 ----------------

# PJ 는 없는 드라이브(예: E:)를 만나면 예외를 던진다.
# 파일 경로는 전부 .NET API 로만 다뤄 예외가 나지 않게 한다.
function PJ([string]$a, [string]$b) { return [System.IO.Path]::Combine($a, $b) }
function FileExists([string]$p) { try { return [System.IO.File]::Exists($p) } catch { return $false } }
function DirExists([string]$p)  { try { return [System.IO.Directory]::Exists($p) } catch { return $false } }

function Wait-Enter {
    Write-Host ''
    Write-Host '계속하려면 Enter 키를 누르세요...' -NoNewline
    [void][Console]::ReadLine()
}

function Abort([string]$msg) {
    Write-Host ''
    Write-Host "[오류] $msg" -ForegroundColor Red
    Wait-Enter
    exit 1
}

function Get-Sha([byte[]]$bytes) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { return ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLower() }
    finally { $sha.Dispose() }
}

function Get-FileSha([string]$path) {
    if (-not (FileExists $path)) { return $null }
    return Get-Sha ([System.IO.File]::ReadAllBytes($path))
}

function Write-Atomic([string]$path, [byte[]]$data) {
    $tmp = "$path.ortmp"
    [System.IO.File]::WriteAllBytes($tmp, $data)
    if (FileExists $path) { [System.IO.File]::Delete($path) }
    [System.IO.File]::Move($tmp, $path)
}

# ---------------- 패치 데이터 ----------------

function Read-PatchFile([string]$path) {
    if (-not (FileExists $path)) {
        Abort "patch.orkp 파일이 없습니다.`n     이 스크립트와 같은 폴더에 patch.orkp 가 있어야 합니다."
    }
    $raw = [System.IO.File]::ReadAllBytes($path)
    if ($raw.Length -lt 16) { Abort 'patch.orkp 가 손상되었습니다.' }
    $magic = [System.Text.Encoding]::ASCII.GetString($raw, 0, 5)
    if ($magic -ne 'ORKP1') { Abort 'patch.orkp 형식이 올바르지 않습니다.' }
    $bodyLen = [System.BitConverter]::ToUInt64($raw, 8)

    # zlib 스트림(2바이트 헤더 + raw deflate)
    $inMs = New-Object System.IO.MemoryStream (,$raw)
    $inMs.Position = 18
    $ds  = New-Object System.IO.Compression.DeflateStream($inMs, [System.IO.Compression.CompressionMode]::Decompress)
    $out = New-Object System.IO.MemoryStream
    $ds.CopyTo($out)
    $ds.Dispose(); $inMs.Dispose()
    if ([uint64]$out.Length -ne $bodyLen) { Abort 'patch.orkp 가 손상되었습니다 (크기 불일치).' }

    $out.Position = 0
    $br = New-Object System.IO.BinaryReader($out)
    $count = $br.ReadUInt32()
    $entries = New-Object System.Collections.ArrayList
    for ($i = 0; $i -lt $count; $i++) {
        $pl  = $br.ReadUInt16()
        $rel = [System.Text.Encoding]::UTF8.GetString($br.ReadBytes($pl))
        $srcHash = ([System.BitConverter]::ToString($br.ReadBytes(32))).Replace('-', '').ToLower()
        $dstHash = ([System.BitConverter]::ToString($br.ReadBytes(32))).Replace('-', '').ToLower()
        $srcSize = $br.ReadUInt64()
        $dstSize = $br.ReadUInt64()
        $opsLen  = $br.ReadUInt32()
        $ops     = $br.ReadBytes($opsLen)
        [void]$entries.Add([pscustomobject]@{
            Rel     = $rel
            Name    = ($rel -split '[\\/]')[-1]
            RelWin  = $rel.Replace('/', [System.IO.Path]::DirectorySeparatorChar)
            SrcHash = $srcHash
            DstHash = $dstHash
            SrcSize = $srcSize
            DstSize = $dstSize
            Ops     = $ops
        })
    }
    $br.Dispose(); $out.Dispose()
    return $entries
}

function Invoke-Delta([byte[]]$src, [byte[]]$ops, [int]$dstSize) {
    $ms  = New-Object System.IO.MemoryStream (,$ops)
    $br  = New-Object System.IO.BinaryReader($ms)
    $out = New-Object System.IO.MemoryStream ($dstSize)
    try {
        $n = $br.ReadUInt32()
        for ($i = 0; $i -lt $n; $i++) {
            $kind = $br.ReadByte()
            if ($kind -eq 1) {
                $off = [int]$br.ReadUInt64()
                $len = [int]$br.ReadUInt32()
                $out.Write($src, $off, $len)
            }
            elseif ($kind -eq 2) {
                $len = [int]$br.ReadUInt32()
                $buf = $br.ReadBytes($len)
                $out.Write($buf, 0, $len)
            }
            else { throw "알 수 없는 연산 코드 $kind" }
        }
        if ($out.Length -ne $dstSize) { throw '결과 크기가 예상과 다릅니다' }
        return $out.ToArray()
    }
    finally { $br.Dispose(); $ms.Dispose(); $out.Dispose() }
}

# ---------------- 게임 폴더 찾기 ----------------

function Test-GameDir([string]$dir) {
    if ([string]::IsNullOrWhiteSpace($dir)) { return $false }
    if (FileExists (PJ $dir 'OddRealm.exe')) { return $true }
    if (DirExists (PJ $dir 'OddRealm_Data')) { return $true }
    return $false
}

function Get-SteamLibraries {
    $roots = New-Object System.Collections.ArrayList
    $seen  = @{}
    function Add-Root([string]$p) {
        if ([string]::IsNullOrWhiteSpace($p)) { return }
        $k = $p.TrimEnd('\').ToLower()
        if (-not $seen.ContainsKey($k)) { $seen[$k] = $true; [void]$roots.Add($p) }
    }

    $bases = New-Object System.Collections.ArrayList
    # 실제로 존재하는 드라이브만 훑는다 (없는 드라이브를 건드리면 예외가 난다)
    $letters = @()
    try {
        foreach ($dv in [System.IO.DriveInfo]::GetDrives()) {
            if ($dv.IsReady) { $letters += $dv.Name.Substring(0, 1).ToUpper() }
        }
    } catch { $letters = @('C') }
    if ($letters.Count -eq 0) { $letters = @('C') }
    foreach ($d in $letters) {
        [void]$bases.Add("${d}:\Program Files (x86)\Steam")
        [void]$bases.Add("${d}:\Program Files\Steam")
        [void]$bases.Add("${d}:\Steam")
        [void]$bases.Add("${d}:\SteamLibrary")
    }
    try {
        $reg = (Get-ItemProperty -Path 'HKCU:\Software\Valve\Steam' -Name SteamPath -ErrorAction SilentlyContinue).SteamPath
        if ($reg) { [void]$bases.Insert(0, ($reg -replace '/', '\')) }
    } catch {}

    foreach ($b in $bases) {
        Add-Root $b
        foreach ($vdf in @((PJ $b 'steamapps\libraryfolders.vdf'), (PJ $b 'config\libraryfolders.vdf'))) {
            if (-not (FileExists $vdf)) { continue }
            foreach ($line in [System.IO.File]::ReadAllLines($vdf)) {
                $t = $line.Trim()
                if (-not $t.StartsWith('"path"')) { continue }
                $parts = $t.Split('"')
                if ($parts.Length -ge 4) { Add-Root ($parts[3] -replace '\\\\', '\') }
            }
        }
    }
    return $roots
}

function Find-Game {
    $d = $ScriptDir
    for ($i = 0; $i -lt 3 -and $d; $i++) {
        if (Test-GameDir $d) { return $d }
        $d = Split-Path -Parent $d
    }
    if (Test-GameDir (Get-Location).Path) { return (Get-Location).Path }
    foreach ($lib in Get-SteamLibraries) {
        try { $p = PJ $lib 'steamapps\common\Odd Realm' } catch { continue }
        if (Test-GameDir $p) { return $p }
    }
    return $null
}

# ---------------- 상태 확인 ----------------

function Get-States([string]$game, $entries) {
    $st = @{}
    foreach ($e in $entries) {
        $full = PJ $game $e.RelWin
        $h = Get-FileSha $full
        if ($null -eq $h)          { $st[$e.Rel] = 'missing' }
        elseif ($h -eq $e.SrcHash) { $st[$e.Rel] = 'original' }
        elseif ($h -eq $e.DstHash) { $st[$e.Rel] = 'patched' }
        else                       { $st[$e.Rel] = 'unknown' }
    }
    return $st
}

function Find-Backup([string]$game, [string]$name, [string]$wantHash) {
    $root = PJ $game $BackupRoot
    if (-not (DirExists $root)) { return $null }
    $subs = @()
    try { $subs = [System.IO.Directory]::GetDirectories($root) } catch { return $null }
    foreach ($dir in $subs) {
        $p = PJ $dir $name
        if (-not (FileExists $p)) { continue }
        $b = [System.IO.File]::ReadAllBytes($p)
        if ((Get-Sha $b) -eq $wantHash) { return $b }
    }
    return $null
}

# ---------------- 동작 ----------------

function Invoke-Install([string]$game, $entries) {
    $st = Get-States $game $entries

    # 이전 버전 한글패치가 깔려 있으면 백업본으로 원복
    $restored = $false
    foreach ($e in $entries) {
        if ($st[$e.Rel] -ne 'unknown') { continue }
        $b = Find-Backup $game $e.Name $e.SrcHash
        if ($null -eq $b) { continue }
        if (-not $restored) {
            Write-Host ''
            Write-Host '이전 버전 한글패치가 발견되었습니다. 원본으로 되돌리는 중...'
            $restored = $true
        }
        Write-Atomic (PJ $game $e.RelWin) $b
        Write-Host "   - $($e.Name) : 원본 복구"
        $st[$e.Rel] = 'original'
    }

    $bad = @()
    $allPatched = $true
    foreach ($e in $entries) {
        switch ($st[$e.Rel]) {
            'missing' { $bad += "$($e.Name)  (파일 없음)" }
            'unknown' { $bad += "$($e.Name)  (다른 게임 버전이거나 이미 다른 패치가 적용됨)" }
        }
        if ($st[$e.Rel] -ne 'patched') { $allPatched = $false }
    }
    if ($bad.Count -gt 0) {
        Write-Host ''
        Write-Host '다음 파일이 이 패치가 지원하는 원본과 다릅니다:'
        foreach ($b in $bad) { Write-Host "   - $b" }
        Write-Host ''
        Write-Host '이 패치는 특정 게임 버전에만 적용됩니다.'
        Write-Host 'Steam → Odd Realm 우클릭 → 속성 → 설치된 파일 → 파일 무결성 검사'
        Write-Host '를 실행해 원본으로 되돌린 뒤 다시 시도해 주세요.'
        Abort '설치를 중단했습니다.'
    }
    if ($allPatched) {
        Write-Host ''
        Write-Host '이미 한글패치가 적용되어 있습니다.'
        return
    }

    $bdir = PJ (PJ $game $BackupRoot) "v$AppVersion"
    try { [void](New-Item -ItemType Directory -Force -Path $bdir) }
    catch { Abort "백업 폴더를 만들 수 없습니다: $($_.Exception.Message)`n     이 스크립트를 관리자 권한으로 실행해 보세요." }

    Write-Host ''
    $i = 0
    foreach ($e in $entries) {
        $i++
        $full = PJ $game $e.RelWin
        Write-Host ("[{0}/{1}] {2}" -f $i, $entries.Count, $e.Name)
        if ($st[$e.Rel] -eq 'patched') { Write-Host '       이미 적용됨, 건너뜁니다'; continue }

        $src = [System.IO.File]::ReadAllBytes($full)
        $bpath = PJ $bdir $e.Name
        if (-not (FileExists $bpath)) {
            Write-Host '       원본 백업 중...'
            try { [System.IO.File]::WriteAllBytes($bpath, $src) }
            catch { Abort "백업 실패: $($_.Exception.Message)`n     관리자 권한으로 실행해 보세요." }
        }

        Write-Host '       패치 적용 중...'
        try { $dst = Invoke-Delta $src $e.Ops ([int]$e.DstSize) }
        catch { Abort "패치 적용 실패 ($($e.Name)): $($_.Exception.Message)" }
        if ((Get-Sha $dst) -ne $e.DstHash) { Abort "패치 결과 검증 실패 ($($e.Name))" }
        try { Write-Atomic $full $dst }
        catch { Abort "쓰기 실패: $($_.Exception.Message)`n     게임이 실행 중이면 종료하고, 관리자 권한으로 실행해 보세요." }
        Write-Host '       완료'
    }
    Write-Host ''
    Write-Host '한글패치 설치가 끝났습니다. 게임을 실행하세요.' -ForegroundColor Green
    Write-Host "원본 파일은 $BackupRoot\v$AppVersion 에 백업되어 있습니다."
}

function Invoke-Restore([string]$game, $entries) {
    $n = 0
    Write-Host ''
    foreach ($e in $entries) {
        $full = PJ $game $e.RelWin
        $b = Find-Backup $game $e.Name $e.SrcHash
        if ($null -eq $b) { Write-Host "   - $($e.Name) : 쓸 수 있는 백업이 없습니다 (건너뜀)"; continue }
        if ((Get-FileSha $full) -eq $e.SrcHash) { Write-Host "   - $($e.Name) : 이미 원본입니다"; continue }
        try { Write-Atomic $full $b }
        catch { Abort "복구 실패 ($($e.Name)): $($_.Exception.Message)" }
        Write-Host "   - $($e.Name) : 복구 완료"
        $n++
    }
    Write-Host ''
    if ($n -eq 0) {
        Write-Host '복구한 파일이 없습니다.'
        Write-Host 'Steam → 속성 → 설치된 파일 → 파일 무결성 검사로도 원본을 되돌릴 수 있습니다.'
    } else {
        Write-Host "$($n)개 파일을 원본으로 되돌렸습니다."
    }
}

function Show-Status([string]$game, $entries) {
    $st = Get-States $game $entries
    Write-Host ''
    foreach ($e in ($entries | Sort-Object Name)) {
        $s = switch ($st[$e.Rel]) {
            'original' { '원본' }
            'patched'  { '한글패치 적용됨' }
            'unknown'  { '알 수 없음 (버전 불일치)' }
            'missing'  { '파일 없음' }
        }
        Write-Host ("   {0,-46}  {1}" -f $e.Name, $s)
    }
}

# ---------------- 메인 ----------------

Write-Host ''
Write-Host "=== $AppName v$AppVersion ==="
Write-Host 'Unity 6000.4.4f1 / Odd Realm 대응'

try {
    $entries = Read-PatchFile (PJ $ScriptDir 'patch.orkp')

    $game = Find-Game
    if (-not $game) {
        Write-Host ''
        Write-Host 'Odd Realm 설치 폴더를 자동으로 찾지 못했습니다.'
        Write-Host '예) C:\Program Files (x86)\Steam\steamapps\common\Odd Realm'
        while ($true) {
            Write-Host ''
            Write-Host '게임 폴더 경로를 붙여넣고 Enter: ' -NoNewline
            $inp = [Console]::ReadLine()
            if ($null -eq $inp) { exit 1 }
            $inp = $inp.Trim().Trim('"').Trim("'")
            if ($inp -eq '') { continue }
            if (Test-GameDir $inp) { $game = $inp; break }
            Write-Host '   그 폴더에서 OddRealm.exe 를 찾을 수 없습니다.'
        }
    }

    Write-Host ''
    Write-Host "게임 폴더: $game"
    Show-Status $game $entries

    while ($true) {
        Write-Host ''
        Write-Host '  1) 한글패치 설치'
        Write-Host '  2) 원본으로 되돌리기'
        Write-Host '  3) 종료'
        Write-Host ''
        Write-Host '번호 선택: ' -NoNewline
        $c = [Console]::ReadLine()
        if ($null -eq $c) { break }
        $c = $c.Trim()
        if     ($c -eq '1') { Invoke-Install $game $entries; Wait-Enter; break }
        elseif ($c -eq '2') { Invoke-Restore $game $entries; Wait-Enter; break }
        elseif ($c -eq '3') { exit 0 }
        else                { Write-Host '   1, 2, 3 중에서 선택해 주세요.' }
    }
}
catch {
    Write-Host ''
    Write-Host "[예상치 못한 오류] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ''
    Write-Host '아래 내용을 그대로 복사해서 제보해 주시면 고칠 수 있습니다.'
    Write-Host "  위치 : $($_.InvocationInfo.ScriptName):$($_.InvocationInfo.ScriptLineNumber)"
    Write-Host "  구문 : $($_.InvocationInfo.Line.Trim())"
    Wait-Enter
    exit 1
}
