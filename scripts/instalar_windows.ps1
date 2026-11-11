# BarFlow - instalacao local para Windows 10/11.
# Baixa Python 3.12.10 somente quando necessario, apos confirmacao,
# diretamente da Python Software Foundation e valida a assinatura digital.
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$root = (Get-Location).Path
$pythonVersion = '3.12.10'
$downloadUrl = 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe'
$localPython = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'
$venvPython = Join-Path $root '.venv\Scripts\python.exe'

function Test-Python312([string]$executable) {
    if (-not $executable -or -not (Test-Path -LiteralPath $executable)) { return $false }
    try {
        $version = & $executable -c 'import sys; print(sys.version_info.major, sys.version_info.minor)' 2>$null
        return (($LASTEXITCODE -eq 0) -and (($version | Select-Object -Last 1).Trim() -eq '3 12'))
    } catch { return $false }
}

function Find-Python312 {
    if (Test-Python312 $localPython) { return $localPython }
    $candidates = @(
        (Join-Path $env:ProgramFiles 'Python312\python.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'Python312-32\python.exe')
    )
    foreach ($candidate in $candidates) { if (Test-Python312 $candidate) { return $candidate } }
    # PEP 514: localiza instalacoes para usuario e para maquina sem depender do PATH.
    foreach ($reg in @('HKCU:\Software\Python\PythonCore\3.12\InstallPath',
                       'HKLM:\Software\Python\PythonCore\3.12\InstallPath',
                       'HKLM:\Software\WOW6432Node\Python\PythonCore\3.12\InstallPath')) {
        try {
            $entry = Get-Item -LiteralPath $reg -ErrorAction Stop
            $candidate = $entry.GetValue('ExecutablePath')
            if (-not $candidate) {
                $dir = $entry.GetValue('')
                if ($dir) { $candidate = Join-Path $dir 'python.exe' }
            }
            if (Test-Python312 $candidate) { return $candidate }
        } catch { }
    }
    try {
        $found = (& py -3.12 -c 'import sys; print(sys.executable)' 2>$null | Select-Object -Last 1)
        if (Test-Python312 $found) { return $found.Trim() }
    } catch { }
    try {
        $found = (& python -c 'import sys; print(sys.executable)' 2>$null | Select-Object -Last 1)
        if (Test-Python312 $found) { return $found.Trim() }
    } catch { }
    return $null
}

try {
    Write-Host '=== Instalador do BarFlow ===' -ForegroundColor Cyan
    Write-Host 'Sistema local, banco SQLite e dependencias Python.'
    if ([Environment]::Is64BitOperatingSystem -eq $false -or $env:PROCESSOR_ARCHITECTURE -eq 'ARM64') {
        throw 'O download automatico deste pacote atende Windows x64. Instale Python 3.12 para sua arquitetura em https://www.python.org/downloads/windows/ e execute novamente.'
    }

    $python = Find-Python312
    if (-not $python) {
        Write-Host "Python 3.12 nao encontrado neste computador." -ForegroundColor Yellow
        Write-Host "Origem oficial: $downloadUrl"
        Write-Host 'A instalacao sera feita para o usuario atual, sem exigir alteracoes globais no PATH.'
        $answer = Read-Host 'Autoriza baixar e instalar Python 3.12.10? (S/N)'
        if ($answer -notmatch '^[sS]([iI][mM])?$') { throw 'Instalacao cancelada pelo usuario. Nenhum download efetuado.' }
        $installer = Join-Path $env:TEMP 'barflow-python-3.12.10-amd64.exe'
        Write-Host 'Baixando instalador oficial do Python...'
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $downloadUrl -OutFile $installer -UseBasicParsing
        $signature = Get-AuthenticodeSignature -LiteralPath $installer
        if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Python Software Foundation') {
            Remove-Item -LiteralPath $installer -Force -ErrorAction SilentlyContinue
            throw 'Assinatura digital invalida ou editor diferente da Python Software Foundation. Instalacao interrompida.'
        }
        Write-Host 'Assinatura digital da Python Software Foundation verificada.' -ForegroundColor Green
        Write-Host 'Instalando Python para o usuario atual...'
        $result = Start-Process -FilePath $installer -ArgumentList '/quiet InstallAllUsers=0 PrependPath=0 Include_pip=1 Include_launcher=1 Include_test=0' -Wait -PassThru
        if ($result.ExitCode -notin @(0, 3010)) { throw "Instalador do Python retornou codigo $($result.ExitCode)." }
        if ($result.ExitCode -eq 3010) { Write-Warning 'O Windows pode precisar de reinicializacao apos a instalacao.' }
        Remove-Item -LiteralPath $installer -Force -ErrorAction SilentlyContinue
        # Verifica o caminho de instalacao explicito e faz nova descoberta (incluindo registro).
        $python = Find-Python312
        if (-not $python) {
            Write-Warning "Caminho esperado: $localPython"
            throw 'Python nao encontrado apos instalacao. Verifique se o antivirus bloqueou python.exe ou se o instalador retornou erro.'
        }
        Write-Host "Python instalado e detectado: $python" -ForegroundColor Green
    } else {
        Write-Host "Python 3.12 encontrado: $python" -ForegroundColor Green
    }

    if (Test-Path -LiteralPath $venvPython) {
        if (-not (Test-Python312 $venvPython)) {
            throw 'O ambiente .venv existente usa uma versao diferente de Python. Faca backup e renomeie a pasta .venv antes de reinstalar.'
        }
        Write-Host 'Ambiente virtual existente sera reutilizado.'
    } else {
        Write-Host 'Criando ambiente virtual isolado (.venv)...'
        & $python -m venv (Join-Path $root '.venv')
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $venvPython)) { throw 'Falha ao criar ambiente virtual Python.' }
    }

    Write-Host 'Instalando dependencias do BarFlow (requer internet)...'
    & $venvPython -m pip install --disable-pip-version-check -r (Join-Path $root 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar dependencias. Verifique internet, proxy ou antivirus.' }

    Write-Host 'Conferindo bibliotecas...'
    & $venvPython -c 'import fastapi,uvicorn,sqlalchemy,argon2,pydantic'
    if ($LASTEXITCODE -ne 0) { throw 'Bibliotecas nao foram importadas corretamente.' }
    Write-Host 'Dependencias essenciais OK' -ForegroundColor Green

    Write-Host 'Configurando acesso inicial do administrador (admin/admin, troca obrigatoria):'
    & $venvPython (Join-Path $root 'scripts\criar_admin.py')
    if ($LASTEXITCODE -ne 0) { throw 'Configuracao do administrador falhou.' }

    Write-Host ''
    Write-Host 'Instalacao concluida! Execute iniciar_windows.bat.' -ForegroundColor Green
    exit 0
} catch {
    Write-Host "FALHA: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
