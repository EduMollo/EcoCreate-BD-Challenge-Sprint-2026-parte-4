# Vídeo narrado — ClyvoVet Database Sprint 4

Sugestão: 9 a 10 minutos. O enunciado informado não fixa duração máxima.

## Preparação antes de gravar

- Oracle FIAP conectado e scripts de verificação aprovados.
- Java iniciado com perfil Oracle, login administrativo funcionando.
- Docker/MongoDB pronto, sem erros pendentes.
- SQL Developer conectado ao mesmo usuário da aplicação.
- Não exibir senhas, `.env` nem detalhes privados da conexão.

## Sequência e falas

1. **Apresentação.** “Este é o ClyvoVet, continuação da Sprint 3, que recebeu nota 100. Nesta etapa organizamos os processos em packages e integramos Oracle, Java e MongoDB.” Mostrar os integrantes na capa.
2. **Modelos.** Mostrar os PDFs lógico e físico. “O Java e os packages trabalham com as mesmas tabelas. As views CV4 apenas adaptam nomes e códigos; não são uma cópia dos dados.” Explicar as entidades retomadas: veterinário, serviço e leitura de sensor.
3. **Modularidade.** Mostrar specification/body dos quatro packages e a fachada. “Os triggers continuam como objetos do Oracle e delegam a lógica reutilizável aos packages.” Abrir USER_ERRORS e status VALID reais.
4. **Inserção pela aplicação.** Cadastrar um pet vinculado a um tutor da carga. Mostrar o ID na interface e consultar o mesmo registro:

```sql
SELECT id,nome,id_tutor,peso_kg FROM tb_pet ORDER BY id DESC;
SELECT id_pet,nome,id_tutor,peso_kg FROM CV4_PET ORDER BY id_pet DESC;
SELECT id_auditoria,id_registro,tipo_operacao,valor_anterior,valor_novo
FROM CV4_AUD_PET ORDER BY id_auditoria DESC;
```

5. **Atendimento.** Agendar com um profissional do catálogo, iniciar e concluir a consulta, registrando valor. “A interface persiste este atendimento no Oracle; a view e o relatório leem o mesmo ID.” Conferir:

```sql
SELECT id,id_pet,status,valor,id_veterinario,id_tipo_servico
FROM tb_consulta ORDER BY id DESC;
SELECT id_atendimento,id_pet,status,valor
FROM CV4_ATENDIMENTO ORDER BY id_atendimento DESC;
```

6. **Procedure de inserção.** Abrir Relatórios → Monitoramento por sensores, registrar uma leitura e conferir em `CV4_LEITURA_SENSOR`. Mostrar `OracleClinicoService.registrarLeitura`: “A aplicação chama PRC_REGISTRAR_LEITURA do package, recebe a chave de saída e confirma a transação.” Calcular o score. “A função preserva o cálculo por sensores da Sprint 3; o painel Java por regras continua separado.”
7. **Relatório.** Consultar faturamento do ano da consulta pela aplicação. Mostrar a chamada JDBC. Explicar subtotal, total e acumulação por cursor. O total da carga original é 15.635,00; novas consultas concluídas alteram o total.
8. **Exportação.** Baixar JSON pela aplicação. Mostrar a chamada `PKG_CLYVOVET.PRC_ATENDIMENTOS_JSON`, o OUT CLOB e o arquivo salvo em `dataset/2TDSPF_2026_Atendimentos.json`. “O arquivo foi produzido por um JOIN de seis entidades, usando nossa conversão manual para JSON.”
9. **MongoDB.** Executar `executar-mongodb.ps1 importar` e `consultar`. Mostrar o documento com entidades aninhadas. “Cada atendimento é um documento. A coleção possui validador e índices por ID, pet e clínica. O importador compara os campos com o JSON original.” Mostrar a consulta de faturamento e explicar os campos derivados BSON.
10. **Repetição e encerramento.** Importar novamente e conferir os totais. “O upsert pela chave de origem evita duplicação. Com isso, demonstramos inserção no relacional, execução dos packages pelo backend e exportação/importação no MongoDB.”

## Conferência final

- Ouvir a narração do início ao fim.
- Conferir que os códigos mostrados são os da entrega.
- Conferir acesso ao link do vídeo em uma janela sem login.
- Não apresentar logs esperados, mocks ou arquivos de exemplo como execução real.
