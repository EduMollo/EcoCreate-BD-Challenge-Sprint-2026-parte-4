$ErrorActionPreference='Stop'
function ConvertTo-OracleJdbcUrl {
    param([AllowEmptyString()][string]$ConnectionText)
    $connectionValue=$ConnectionText.Trim()
    if([string]::IsNullOrWhiteSpace($connectionValue)) {
        return 'jdbc:oracle:thin:@oracle.fiap.com.br:1521:orcl'
    }
    if($connectionValue -match '[\r\n]') { throw 'A conexao nao pode conter quebras de linha.' }
    if($connectionValue -match '^jdbc:oracle:thin:@\S+$') { return $connectionValue }
    # Forma curta do SQL Developer: host porta SID (ex.: oracle.fiap.com.br 1521 orcl).
    if($connectionValue -match '^(?<host>[a-zA-Z0-9.-]+)\s+(?<port>\d{1,5})\s+(?<sid>[a-zA-Z0-9_.-]+)$') {
        $oracleHost=$Matches['host']; $oraclePort=[int]$Matches['port']; $oracleSid=$Matches['sid']
        if($oraclePort -lt 1 -or $oraclePort -gt 65535) { throw 'A porta Oracle deve estar entre 1 e 65535.' }
        return "jdbc:oracle:thin:@${oracleHost}:${oraclePort}:${oracleSid}"
    }
    throw 'Use host porta SID, uma URL JDBC completa ou Enter para a conexao FIAP padrao.'
}
$connectionInput=Read-Host 'Conexao Oracle (Enter = FIAP; ou host porta SID; ou URL JDBC completa)'
$url=ConvertTo-OracleJdbcUrl $connectionInput
Write-Host "Conexao selecionada: $url"
$username=Read-Host 'Usuario Oracle FIAP'
if([string]::IsNullOrWhiteSpace($username) -or $username -match '[\r\n]') { throw 'Informe um usuario Oracle valido.' }
$password=Read-Host 'Senha Oracle FIAP (oculta)' -AsSecureString
$admin=Read-Host 'Senha inicial do administrador ClyvoVet (minimo 12 caracteres, oculta)' -AsSecureString
$plainPassword=[Net.NetworkCredential]::new('', $password).Password
$plainAdmin=[Net.NetworkCredential]::new('', $admin).Password
if([string]::IsNullOrWhiteSpace($username) -or [string]::IsNullOrEmpty($plainPassword)) { throw 'Usuario e senha Oracle obrigatorios.' }
if($plainAdmin.Length -lt 12) { throw 'A senha inicial do administrador deve ter ao menos 12 caracteres.' }
foreach($value in @($url,$username,$plainPassword,$plainAdmin)) {
    if($value -match '[\r\n]') { throw 'Os valores nao podem conter quebras de linha.' }
}
$destination=Join-Path $PSScriptRoot '.env'
[IO.File]::WriteAllLines($destination,@("DB_URL=$url","DB_USERNAME=$username","DB_PASSWORD=$plainPassword",'ADMIN_USERNAME=admin',"ADMIN_PASSWORD=$plainAdmin"),[Text.UTF8Encoding]::new($false))
$plainPassword=$null
$plainAdmin=$null
Write-Host 'Acesso salvo localmente. O .env fica fora do Git e do pacote de entrega.'
