# Validacao tecnica — 01/11/2026

A sequencia real foi concluida no terminal Windows em 01/11/2026, as 16:19 (horario de Sao Paulo). Os resultados foram conferidos no arquivo do roteiro, no JSON exportado e nos relatorios JUnit/Surefire. O resumo limpo, sem credenciais nem dados privados do computador, esta em `2TDSPF_2026_Validacao.json`.

| Parte | Resultado |
|---|---|
| Oracle FIAP 19.3 | Conexao confirmada, servico orcl |
| Objetos PL/SQL | 12 objetos finais VALID; USER_ERRORS vazio |
| Carga e testes | Carga preservada; excecoes esperadas e testes transacionais aprovados, com rollback |
| Dataset Oracle | 34 documentos reais; 30 realizados em 2026, total 15.635,00 |
| MongoDB | Importacao, comparacao de conteudo, consultas, indices e reimportacao aprovados; 34 documentos sem duplicacao |
| Java | Build completo com o pom.xml real; JAR executavel gerado |
| JUnit | 40 testes identificados: 38 executados, zero falhas/erros, 2 opcionais PostgreSQL ignorados |
| Integracao Oracle Java | Os 2 testes OracleIntegracaoTest foram executados e aprovaram chamadas reais de exportacao e faturamento |
| Compatibilidade mongosh | 4 testes locais adicionais aprovados, cobrindo criacao, colecao existente, collMod rejeitado e reimportacao |

SHA-256 do dataset: `1c5e23089fe23ae726af5c594beb4bad5899a033475fcc098fb17f25430bc04c`.

Os testes Java comprovam chamadas reais das procedures de relatorios pelo backend, usando a base Oracle da aplicacao. Os testes de contrato das leituras verificam os parametros JDBC. O teste SQL cobre insercao de leitura e auditoria com rollback. A jornada completa pela interface ainda precisa ser conferida e demonstrada no video.

## Pendencias para submissao

1. Abrir a aplicacao com o perfil Oracle e conferir login, cadastro de pet, atendimento, registro de leitura e exportacao pelas telas.
2. Gravar o video narrado seguindo ROTEIRO-VIDEO.md e conferir o acesso do professor ao link.
3. Incluir o link em docs/VIDEO.md e recriar o pacote com `py tools/empacotar_entrega.py --video-url "LINK_HTTPS_DO_VIDEO"`.

## Fechamento tecnico complementar

A revisao local conferiu os modelos PDF, os SQLs integrados, a identidade entre migrations Oracle e scripts Database e o hash do JSON real de 34 documentos. Os quatro testes de compatibilidade mongosh passaram novamente.

O Java recebeu quatro testes MVC adicionais das telas Oracle e os seis cenarios Playwright foram executados com sucesso em H2. Os fontes Oracle atuais serao entregues pelo mesmo repositorio Java indicado em docs/BACKEND-JAVA.md. Resumo do fechamento em docs/FECHAMENTO-TECNICO.json.

A nova tentativa de conexao Oracle pelo agente foi bloqueada pela permissao de rede do ambiente; ela nao substitui nem invalida a execucao real acima. A demonstracao Oracle pela interface faz parte da gravacao da equipe. Os testes de tela substituem o servico de banco por contrato e nao sao apresentados como nova execucao PL/SQL.

A versao publicada em PostgreSQL continua separada e nao demonstra PL/SQL. O video de Database deve usar a aplicacao conectada ao Oracle FIAP. As configuracoes locais .env e logs brutos privados ficam fora do ZIP.
