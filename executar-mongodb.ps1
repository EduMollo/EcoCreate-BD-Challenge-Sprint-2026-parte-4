param([ValidateSet('iniciar','importar','consultar','parar')][string]$Acao='iniciar')
$ErrorActionPreference='Stop'
$compose=Join-Path $PSScriptRoot 'mongodb\docker-compose.yml'
function Docker-Ok {
    param([string[]]$DockerArgs)
    & docker @DockerArgs
    if($LASTEXITCODE -ne 0) { throw 'Docker/MongoDB interrompido. Confira a mensagem acima.' }
}
if($Acao -eq 'iniciar') {
    New-Item -ItemType Directory -Force -Path (Join-Path $PSScriptRoot 'dataset') | Out-Null
    Docker-Ok -DockerArgs @('compose','-f',$compose,'up','-d','--wait','--wait-timeout','180')
} elseif($Acao -eq 'importar') {
    $dataset=Join-Path $PSScriptRoot 'dataset\2TDSPF_2026_Atendimentos.json'
    if(-not (Test-Path -LiteralPath $dataset)) { throw 'Exporte primeiro o JSON real usando executar-oracle.ps1 export ou a aplicacao.' }
    # Inicia tambem se ainda estiver parado, mantendo os volumes existentes.
    Docker-Ok -DockerArgs @('compose','-f',$compose,'up','-d','--wait','--wait-timeout','180')
    Docker-Ok -DockerArgs @('compose','-f',$compose,'exec','-T','mongodb','mongosh','--quiet','--file','/scripts/01_criar_estrutura.js')
    Docker-Ok -DockerArgs @('compose','-f',$compose,'exec','-T','mongodb','mongosh','--quiet','--file','/scripts/02_importar_validar.js')
} elseif($Acao -eq 'consultar') {
    Docker-Ok -DockerArgs @('compose','-f',$compose,'exec','-T','mongodb','mongosh','--quiet','--file','/scripts/03_consultas.js')
} else { Docker-Ok -DockerArgs @('compose','-f',$compose,'stop') }
