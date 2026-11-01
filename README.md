# ClyvoVet — Database Sprint 4

Continuação da Sprint 3, avaliada com **100/100**, com feedback “parabéns”. Entrega em **04/11/2026**. Turma **2TDSPF**.

| Integrante | RM |
|---|---|
| Carlos Alberto Guedes Neto | 566022 |
| Eduardo Novaes Mollo | 561515 |
| Luan Peixoto Marins Rocha | 562258 |
| Mathaus Victor Souza Marcelino | 564146 |
| Vinicius Luis Exposito Morassi | 563340 |

## Entregáveis

| Item | Arquivo |
|---|---|
| Documento principal | `docs/2TDSPF_2026_Proj_BD.pdf` |
| Modelo lógico | `docs/2TDSPF_2026_Modelo_Logico.pdf` |
| Modelo físico com dicionário completo | `docs/2TDSPF_2026_Modelo_Fisico.pdf` |
| Instalação SQL integrada | `sql/2TDSPF_2026_CodigoSql_Integrantes.sql` |
| Packages e gatilhos | `sql/07_packages_gatilhos.sql` |
| Carga fictícia e testes | `sql/09_dados_demonstracao.sql`, `10_verificar_objetos.sql`, `11_testes_transacionais.sql` |
| Dataset real | `dataset/2TDSPF_2026_Atendimentos.json`, exportado do Oracle FIAP: 34 documentos |
| MongoDB | `mongodb/01_criar_estrutura.js`, `02_importar_validar.js`, `03_consultas.js` |
| Vídeo narrado | Gravação pendente; link em `docs/VIDEO.md`, roteiro em `docs/ROTEIRO-VIDEO.md` |

**Validação técnica concluída em 01/11/2026:** Oracle com 12 objetos finais VALID; JSON real de 34 atendimentos; importação e reimportação MongoDB sem duplicatas; build Java completo com 38 testes executados, zero falhas e dois testes opcionais PostgreSQL ignorados. Os testes Oracle foram executados. Resumo verificável em `docs/2TDSPF_2026_Validacao.json`.

O pacote técnico está em `entrega/2TDSPF_2026_ClyvoVet_Database_Sprint4.zip`. A gravação narrada e a demonstração pelas telas Oracle serão feitas pela equipe. Preencher `docs/VIDEO.md` antes da submissão. Conferir `docs/VALIDACAO.md` e `docs/FECHAMENTO-TECNICO.json`. O backend completo está no GitHub; instruções em `docs/BACKEND-JAVA.md`.

## Decisões

1. O Oracle da FIAP é a origem da avaliação. A versão publicada em PostgreSQL não demonstra PL/SQL.
2. As entidades aprovadas são preservadas e evoluídas para o modelo do Java. O JPA usa tabelas `TB_*`; os packages usam views `CV4_*` sobre **as mesmas linhas**. Veterinários, serviços e sensores são entidades próprias com FKs reais.
3. Os prefixos CV4 também alcançam constraints e índices para permitir coexistência com a Sprint 3 no mesmo usuário. Não há DROP no instalador.
4. Mantida a conversão manual JSON e a acumulação manual do faturamento. O retorno agora usa OUT CLOB; erros são propagados com códigos Oracle.
5. Triggers ficam como objetos próprios, delegando a lógica aos packages. Auditoria acompanha a mesma transação da alteração.
6. MongoDB recebe documentos por atendimento, com entidades relacionadas aninhadas. O importador compara campos e contagens e faz upsert sem duplicar IDs. Oracle continua como fonte dos dados.

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

## Documentação e pacote final

As fontes HTML, SVG e geradores Python sem dependências ficam disponíveis para revisão. Para regenerar os PDFs:

```powershell
python tools/gerar_documentacao.py
python tools/renderizar_pdf.py
```

O diretório `historico` preserva o SQL e PDF da entrega aprovada. Ele não é executado na instalação nova.

O vídeo deve ter narração. A execução real Oracle/MongoDB e o JSON exportado já estão registrados; mostrar esses processos pela aplicação durante a gravação. Não considerar o roteiro como vídeo entregue.

Depois de publicar o vídeo, executar `py tools/empacotar_entrega.py --video-url "LINK_HTTPS_DO_VIDEO"`. O comando atualiza o link e recria o pacote. A gravação deve usar Oracle FIAP; o deploy PostgreSQL não executa PL/SQL.
