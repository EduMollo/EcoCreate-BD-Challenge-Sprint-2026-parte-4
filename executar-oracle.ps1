param([ValidateSet('config','check','prepare','install','seed','test','export','app')][string]$Acao='check')
$ErrorActionPreference='Stop'
if(-not $env:JAVA_HOME -and (Test-Path -LiteralPath 'C:\Program Files\Java\jdk-21\bin\java.exe')) {
    $env:JAVA_HOME='C:\Program Files\Java\jdk-21'
}
# Le somente o .env desta entrega. O arquivo nao entra no ZIP nem no Git.
$config=Join-Path $PSScriptRoot '.env'
if(Test-Path -LiteralPath $config) {
    foreach($line in [IO.File]::ReadAllLines($config)) {
        if($line -match '^\s*(DB_URL|DB_USERNAME|DB_PASSWORD|ADMIN_USERNAME|ADMIN_PASSWORD)\s*=(.*)$') {
            [Environment]::SetEnvironmentVariable($Matches[1],$Matches[2],'Process')
        }
    }
}
if($Acao -eq 'config') {
    if(-not $env:DB_URL -or -not $env:DB_USERNAME -or -not $env:DB_PASSWORD) { throw 'A configuracao Oracle local esta incompleta.' }
    return
}
if(-not $env:DB_URL) { $env:DB_URL=Read-Host 'URL JDBC Oracle (a mesma conexao do SQL Developer)' }
if(-not $env:DB_USERNAME) { $env:DB_USERNAME=Read-Host 'Usuario Oracle FIAP' }
if(-not $env:DB_PASSWORD) {
    $secret=Read-Host 'Senha Oracle (oculta)' -AsSecureString
    $env:DB_PASSWORD=[Net.NetworkCredential]::new('', $secret).Password
}
$javaCommand='java'
if($env:JAVA_HOME -and (Test-Path -LiteralPath (Join-Path $env:JAVA_HOME 'bin\java.exe'))) {
    $javaCommand=Join-Path $env:JAVA_HOME 'bin\java.exe'
}
if($Acao -eq 'app') {
    $javaRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\CS4 JAVA\Projeto-EcoCreate-Java-Challenge-Sprint-2026-parte-4'))
    if(-not $env:ADMIN_PASSWORD) {
        $secret=Read-Host 'Senha inicial do administrador (minimo 12 caracteres)' -AsSecureString
        $env:ADMIN_PASSWORD=[Net.NetworkCredential]::new('', $secret).Password
    }
    $env:SPRING_PROFILES_ACTIVE='oracle'
    $env:COOKIE_SECURE='false'
    # Este roteiro usa a instalacao manual validada antes de iniciar a aplicacao.
    $env:ORACLE_FLYWAY_ENABLED='false'
    Push-Location -LiteralPath $javaRoot
    try {
        $jarPath=Join-Path $javaRoot 'target\clyvovet-web-4.0.0.jar'
        if(Test-Path -LiteralPath $jarPath) {
            $latestSource=Get-ChildItem -LiteralPath (Join-Path $javaRoot 'src') -Recurse -File |
              Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
            $jarItem=Get-Item -LiteralPath $jarPath
            $pomItem=Get-Item -LiteralPath (Join-Path $javaRoot 'pom.xml')
            if($jarItem.LastWriteTimeUtc -ge $latestSource.LastWriteTimeUtc -and $jarItem.LastWriteTimeUtc -ge $pomItem.LastWriteTimeUtc) {
                Write-Host 'Iniciando o JAR validado com perfil Oracle em http://localhost:8080.'
                & $javaCommand -jar $jarPath
                exit $LASTEXITCODE
            }
        }
        $env:MAVEN_USER_HOME=Join-Path $env:TEMP 'clyvovet-maven'
        & '.\mvnw.cmd' "-Dmaven.repo.local=$(Join-Path $env:TEMP 'clyvovet-m2')" spring-boot:run
        exit $LASTEXITCODE
    } finally { Pop-Location }
}
$jarRoots=@((Join-Path $env:TEMP 'clyvovet-m2\com\oracle\database\jdbc\ojdbc11'),(Join-Path $env:LOCALAPPDATA 'Temp\clyvovet-m2\com\oracle\database\jdbc\ojdbc11'),(Join-Path $env:USERPROFILE '.m2\repository\com\oracle\database\jdbc\ojdbc11'))
$driver=$null
foreach($jarRoot in $jarRoots) {
    if(Test-Path -LiteralPath $jarRoot) {
        $driver=Get-ChildItem -LiteralPath $jarRoot -Filter 'ojdbc11-*.jar' -Recurse -File |
          Where-Object Name -NotMatch 'sources|javadoc' | Sort-Object FullName -Descending | Select-Object -First 1
        if($driver) { break }
    }
}
if(-not $driver) { throw 'Driver JDBC ausente. Compile primeiro o projeto Java com verificar.ps1.' }
$javaCommand='java'
if($env:JAVA_HOME -and (Test-Path -LiteralPath (Join-Path $env:JAVA_HOME 'bin\java.exe'))) {
    $javaCommand=Join-Path $env:JAVA_HOME 'bin\java.exe'
} elseif(Test-Path -LiteralPath 'C:\Program Files\Java\jdk-21\bin\java.exe') {
    $javaCommand='C:\Program Files\Java\jdk-21\bin\java.exe'
}
& $javaCommand --class-path $driver.FullName (Join-Path $PSScriptRoot 'tools\OracleSprint4.java') $PSScriptRoot $Acao
if($LASTEXITCODE -ne 0) { throw "Oracle interrompido (acao: $Acao). Corrija a causa antes de continuar." }
