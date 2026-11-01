# Backend Java da demonstracao

Fontes: https://github.com/EduMollo/Projeto-EcoCreate-Java-Challenge-Sprint-2026-parte-4

O repositorio inclui o perfil Oracle vigente, migrations, OracleClinicoService,
OracleClinicoController, formulario de sensores, auditoria e testes.
As branches main e develop contem os fontes da entrega.

Para usar os scripts, manter as pastas irmas:

- CS4 DB/EcoCreate-BD-Challenge-Sprint-2026-parte-4
- CS4 JAVA/Projeto-EcoCreate-Java-Challenge-Sprint-2026-parte-4

Compilar o Java antes da demonstracao. Na pasta Database, executar:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\executar-oracle.ps1 app
```

O comando usa as credenciais locais e ORACLE_FLYWAY_ENABLED=false sobre o schema
ja instalado manualmente. Nao reinstalar nem repetir a carga antes do video.
Abrir http://localhost:8080 e entrar com o administrador configurado.
Demonstrar cadastro, atendimento, Relatorios e Monitoramento por sensores.
O roteiro inclui SELECTs para conferir os mesmos IDs em TB_* e CV4_*.

https://clyvovet.vercel.app usa PostgreSQL para a publicacao Java.
Ele nao substitui o Oracle FIAP nem comprova execucao PL/SQL.
