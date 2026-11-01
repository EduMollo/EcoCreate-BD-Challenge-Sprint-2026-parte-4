param([switch]$SomenteOracle,[switch]$SemBuild,[switch]$Retomar)
$ErrorActionPreference='Stop'
if(-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot '.env'))) {
    throw 'Configure primeiro o acesso com configurar-oracle.ps1.'
}
$evidenceRoot=Join-Path $PSScriptRoot 'evidencias'
New-Item -ItemType Directory -Force -Path $evidenceRoot | Out-Null
$transcript=Join-Path $evidenceRoot 'execucao-real.log'
$resultPath=Join-Path $evidenceRoot 'resultado-validacao.json'
$previousResult=$null
$datasetPath=Join-Path $PSScriptRoot 'dataset\2TDSPF_2026_Atendimentos.json'
if($Retomar) {
    if(-not (Test-Path -LiteralPath $resultPath)) { throw 'Nao ha resultado anterior. Execute sem -Retomar.' }
    $previousResult=Get-Content -Raw -LiteralPath $resultPath | ConvertFrom-Json
    if($previousResult.oracle -ne 'aprovado' -or -not (Test-Path -LiteralPath $datasetPath)) {
        throw 'Nao ha etapa Oracle aprovada com dataset salvo. Execute sem -Retomar.'
    }
    if($previousResult.dataset_sha256 -and $previousResult.dataset_sha256 -ne (Get-FileHash -LiteralPath $datasetPath -Algorithm SHA256).Hash) {
        throw 'O dataset mudou desde a ultima validacao. Execute sem -Retomar para conferir a origem novamente.'
    }
}
$result=[ordered]@{
    inicio=(Get-Date).ToString('o')
    oracle='pendente'
    mongodb='pendente'
    build_java='pendente'
    etapa='oracle'
    sucesso=$false
}
$exitCode=0
function Test-DockerReady {
    $previousErrorAction=$ErrorActionPreference
    try {
        $ErrorActionPreference='Continue'
        & docker info --format '{{.ServerVersion}}' 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } finally { $ErrorActionPreference=$previousErrorAction }
}
Start-Transcript -LiteralPath $transcript -Append | Out-Null
try {
    if($Retomar) {
        Write-Host '1/3 - Oracle FIAP: resultado aprovado preservado; retomando as etapas pendentes.'
        & (Join-Path $PSScriptRoot 'executar-oracle.ps1') config
        $result.oracle_validado_em=$previousResult.fim
    } else {
        Write-Host '1/3 - Oracle FIAP: conexao, instalacao protegida, carga, testes e exportacao.'
        & (Join-Path $PSScriptRoot 'executar-oracle.ps1') prepare
    }
    $result.oracle='aprovado'
    $result.dataset_sha256=(Get-FileHash -LiteralPath $datasetPath -Algorithm SHA256).Hash

    if(-not $SomenteOracle -and $Retomar -and $previousResult.mongodb -eq 'aprovado' -and $previousResult.dataset_sha256 -eq $result.dataset_sha256) {
        Write-Host '2/3 - MongoDB: resultado aprovado preservado para o mesmo dataset.'
        $result.mongodb='aprovado'
    } elseif(-not $SomenteOracle) {
        $result.etapa='mongodb'
        Write-Host '2/3 - MongoDB: inicializacao, importacao, consultas e reimportacao.'
        if(-not (Test-DockerReady)) {
            & docker desktop start --detach
            $ready=$false
            for($attempt=0;$attempt -lt 30;$attempt++) {
                if(Test-DockerReady) { $ready=$true; break }
                Start-Sleep -Seconds 2
            }
            if(-not $ready) {
                throw 'O engine Docker ainda nao iniciou. Abra o Docker Desktop, conclua eventuais etapas iniciais e execute novamente. O Oracle ja foi preservado e o JSON fica salvo.'
            }
        }
        & (Join-Path $PSScriptRoot 'executar-mongodb.ps1') importar
        & (Join-Path $PSScriptRoot 'executar-mongodb.ps1') consultar
        & (Join-Path $PSScriptRoot 'executar-mongodb.ps1') importar
        $result.mongodb='aprovado'
    } else { $result.mongodb='nao executado: SomenteOracle' }

    if(-not $SemBuild) {
        $result.etapa='build_java'
        Write-Host '3/3 - Java: build completo e testes, incluindo integracao Oracle.'
        $javaRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\CS4 JAVA\Projeto-EcoCreate-Java-Challenge-Sprint-2026-parte-4'))
        $env:ORACLE_FLYWAY_ENABLED='false'
        $env:RUN_ORACLE_TESTS='true'
        $env:MAVEN_USER_HOME=Join-Path $env:LOCALAPPDATA 'Temp\clyvovet-maven'
        $repoCache=Join-Path $env:LOCALAPPDATA 'Temp\clyvovet-m2'
        Push-Location -LiteralPath $javaRoot
        try {
            & '.\mvnw.cmd' "-Dmaven.repo.local=$repoCache" clean verify
            if($LASTEXITCODE -ne 0) { throw 'O build Java falhou; conferir os detalhes em evidencias/execucao-real.log.' }
        } finally { Pop-Location }
        $result.build_java='aprovado'
    } else { $result.build_java='nao executado: SemBuild' }

    $result.etapa='concluido'
    $result.sucesso=$true
    Write-Host 'Verificacoes solicitadas concluidas. Os resultados foram salvos para conferencia.'
} catch {
    $exitCode=1
    $result.erro=$_.Exception.Message
    Write-Host ('Interrompido na etapa '+$result.etapa+': '+$_.Exception.Message) -ForegroundColor Red
} finally {
    $result.fim=(Get-Date).ToString('o')
    $result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $resultPath -Encoding UTF8
    Stop-Transcript | Out-Null
}
Write-Host "Resultado: $resultPath"
Write-Host 'Nao envie o .env nem suas senhas. Basta avisar que o comando terminou.'
exit $exitCode
