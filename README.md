# ClyvoVet — Database Sprint 4

Continuação da Sprint 3, avaliada com **100/100**, com feedback “parabéns”. Entrega em **04/11/2026**. Turma **2TDSPF**.

| Integrante | RM |
|---|---|
| Carlos Alberto Guedes Neto | 566022 |
| Eduardo Novaes Mollo | 561515 |
| Luan Peixoto Marins Rocha | 562258 |
| Mathaus Victor Souza Marcelino | 564146 |
| Vinicius Luis Exposito Morassi | 563340 |

**🎬 Vídeo demonstrativo** · [](https://www.youtube.com/watch?v=e19eRJnnAcA)

## Primeiro acesso

No PowerShell, dentro desta pasta:

```powershell
.\configurar-oracle.ps1
.\executar-oracle.ps1 check
```

O primeiro comando pede os dados **localmente**, com senhas ocultas, e cria um `.env` que não entra no Git/ZIP. Usar a URL JDBC equivalente à conexão do SQL Developer. O script não tenta adivinhar host ou service name.

Requer Oracle 19c+ e privilégios de criação de tabelas, views, sequences, packages e triggers, além de quota de tablespace. O driver JDBC é reutilizado do cache Maven do projeto Java. O executor JDBC (`tools/OracleSprint4.java`) compila automaticamente com Java 17+.

## Instalação e teste

Para executar a sequência completa no terminal do Windows, inclusive MongoDB e build Java, usar:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\validar-fiap.ps1"
```

O comando verifica se esta versão já está instalada, instala somente quando não existem suas tabelas, carrega dados somente se as tabelas de negócio estão vazias, executa os testes e exporta o JSON. Depois importa no MongoDB, verifica a reimportação e executa o build Java completo. Instalação parcial ou nomes ocupados interrompem o processo, sem apagar objetos.

O resultado fica em `evidencias/resultado-validacao.json`, com log em `evidencias/execucao-real.log`. Se uma etapa falhar, as anteriores ficam registradas e os dados preservados. Para continuar após uma etapa Oracle já aprovada, acrescentar `-Retomar`: o comando reaproveita o dataset e verifica seu hash quando já registrado. Uma etapa MongoDB aprovada também é preservada se o dataset não mudou. `-SomenteOracle` e `-SemBuild` permitem executar um subconjunto explicitamente, sem apresentá-lo como validação integral.

O caminho recomendado para a conta FIAP é a instalação manual controlada:

```powershell
.\executar-oracle.ps1 install
.\executar-oracle.ps1 seed
.\executar-oracle.ps1 test
.\executar-oracle.ps1 export
```

`install` cria tabelas, views, packages, gatilhos e catálogos fictícios. `seed` adiciona uma vez os dados da carga anterior adaptados ao Java: 6 clínicas, 8 tutores, 10 pets, 34 atendimentos e 20 leituras. A trigger gera a auditoria dos pets. O faturamento esperado de 2026 é **15.635,00**, com 30 atendimentos realizados, antes de novas operações.

O instalador interrompe se detectar objetos desta versão. Não executar outra vez sobre uma instalação concluída. A carga também não é feita para repetição: as PKs impedem duplicação. A DDL Oracle faz commits implícitos; instalação parcialmente falha precisa de revisão, não de execução cega ou de DROP em massa.

Os testes SQL provocam exceções de forma controlada e verificam UPDATE, INSERT, DELETE e rollback da auditoria. A exportação usa o package real, com JDBC, e salva o CLOB como UTF-8.

Também é possível executar o SQL integrado no SQL Developer com **F5**. Depois executar somente `09_dados_demonstracao.sql`, `10_verificar_objetos.sql` e `11_testes_transacionais.sql`. Os arquivos 01 a 08 já estão incorporados ao integrado.

## Aplicação Java

A integração está no projeto irmão `CS4 JAVA/Projeto-EcoCreate-Java-Challenge-Sprint-2026-parte-4`.

```powershell
.\executar-oracle.ps1 app
```

Esse comando usa o perfil `oracle` e desativa o Flyway porque a instalação anterior foi manual. Acessar `http://localhost:8080` e entrar com `admin` e a senha inicial escolhida. A senha só inicializa uma conta nova; não troca a senha de uma conta existente.

- Cadastro e atendimento: mesmos dados consultados pelos packages.
- `/relatorios`: exportação JSON e faturamento.
- `/relatorios/oracle`: registro de leituras, cálculo de risco e auditoria.
- Agendamento: no Oracle, selecionar um profissional do catálogo.

O perfil Oracle possui migrations próprias em `db/oracle-sprint4`. **Não misturar instalação manual e Flyway no mesmo schema.** A inicialização automática por Flyway é uma alternativa somente para um schema novo, sem os objetos da aplicação; não é necessária para o roteiro FIAP.

Para exportar **pelo backend no vídeo**, usar o botão Baixar JSON e salvar o arquivo com o nome `2TDSPF_2026_Atendimentos.json` na pasta `dataset` antes da importação.

## MongoDB local

Abrir o Docker Desktop e esperar o engine Linux ficar pronto. Depois:

```powershell
.\executar-mongodb.ps1 iniciar
.\executar-mongodb.ps1 importar
.\executar-mongodb.ps1 consultar
.\executar-mongodb.ps1 importar   # repetir: conferir que nao duplicou IDs
```

Banco: `clyvovet_sprint4`, coleção: `atendimentos`. Imagem oficial `mongodb/mongodb-community-server:8.0-ubi8`; porta exposta somente em `127.0.0.1:27017`, volume persistente. Para encerrar sem apagar dados: `.\executar-mongodb.ps1 parar`.

O código cria a coleção e seus validadores/índices antes de importar. Usa `mongosh` e lê diretamente o JSON exportado; não depende de `mongoimport`. Acrescenta `data_bson` e `valor_decimal`, preservando todos os campos originais. Reimportação atualiza os IDs contidos no arquivo, sem excluir documentos ausentes.

