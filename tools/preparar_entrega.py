"""Gera os scripts Sprint 4 a partir da entrega aprovada, sem executar SQL remoto."""
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[1]
ANTERIOR = ROOT.parent / 'EcoCreate-BD-Challenge-Sprint-2026-parte-3'
JAVA = WORKSPACE / 'CS4 JAVA' / 'Projeto-EcoCreate-Java-Challenge-Sprint-2026-parte-4'
ORACLE = JAVA / 'src/main/resources/db/oracle'

def write(name, text):
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + '\n', encoding='utf-8')

old = (ANTERIOR / 'sql/2TDSPF_2026_CodigoSql_Integrantes.sql').read_text(encoding='utf-8')
(ROOT / 'historico').mkdir(exist_ok=True)
shutil.copyfile(ANTERIOR / 'sql/2TDSPF_2026_CodigoSql_Integrantes.sql', ROOT / 'historico/2TDSPF_2026_CodigoSql_Sprint3.sql')
shutil.copyfile(ANTERIOR / 'docs/2TDSPF_2026_Proj_BD.pdf', ROOT / 'historico/2TDSPF_2026_Proj_BD_Sprint3.pdf')

extension = r"""
-- Sprint 4: complementos do modelo Java; nao remove tabelas/dados anteriores.
-- Executar somente depois das migrations Oracle V1 a V5, em schema de teste.
CREATE TABLE VETERINARIO (
 id_veterinario NUMBER(6) CONSTRAINT pk_veterinario PRIMARY KEY,
 nome VARCHAR2(100) NOT NULL, crmv VARCHAR2(20) NOT NULL,
 especialidade VARCHAR2(60),
 CONSTRAINT uk_veterinario_crmv UNIQUE(crmv));
CREATE UNIQUE INDEX uk_veterinario_nome ON VETERINARIO(UPPER(TRIM(nome)));
CREATE SEQUENCE SEQ_VETERINARIO START WITH 1000 NOCACHE;
CREATE TABLE TIPO_SERVICO (
 id_tipo_servico NUMBER(6) CONSTRAINT pk_tipo_servico PRIMARY KEY,
 descricao VARCHAR2(60) NOT NULL, preco_base NUMBER(10,2) NOT NULL,
 codigo_app VARCHAR2(30) NOT NULL,
 CONSTRAINT ck_tipo_servico_preco CHECK(preco_base > 0));
CREATE TABLE LEITURA_SENSOR (
 id_leitura NUMBER(10) CONSTRAINT pk_leitura PRIMARY KEY,
 id_pet NUMBER(19) NOT NULL CONSTRAINT fk_leitura_pet REFERENCES tb_pet(id),
 dispositivo VARCHAR2(30) NOT NULL, data_hora TIMESTAMP NOT NULL,
 temperatura NUMBER(4,1) NOT NULL, freq_cardiaca NUMBER(4) NOT NULL,
 spo2 NUMBER(5,1) NOT NULL, atividade NUMBER(5,1) NOT NULL,
 CONSTRAINT ck_leitura_temp CHECK(temperatura BETWEEN 20 AND 50),
 CONSTRAINT ck_leitura_fc CHECK(freq_cardiaca BETWEEN 1 AND 400),
 CONSTRAINT ck_leitura_spo2 CHECK(spo2 BETWEEN 0 AND 100),
 CONSTRAINT ck_leitura_atividade CHECK(atividade BETWEEN 0 AND 100));
CREATE SEQUENCE SEQ_LEITURA START WITH 1000 NOCACHE;
CREATE INDEX ix_leitura_pet_data ON LEITURA_SENSOR(id_pet, data_hora);
ALTER TABLE tb_consulta ADD (id_veterinario NUMBER(6), id_tipo_servico NUMBER(6));
ALTER TABLE tb_consulta ADD CONSTRAINT fk_consulta_veterinario FOREIGN KEY(id_veterinario) REFERENCES VETERINARIO;
ALTER TABLE tb_consulta ADD CONSTRAINT fk_consulta_servico FOREIGN KEY(id_tipo_servico) REFERENCES TIPO_SERVICO;
ALTER TABLE tb_consulta MODIFY (id_veterinario NOT NULL,id_tipo_servico NOT NULL);
CREATE INDEX ix_consulta_veterinario ON tb_consulta(id_veterinario);
CREATE INDEX ix_consulta_servico ON tb_consulta(id_tipo_servico);
ALTER TABLE AUD_PET ADD (nome_tabela VARCHAR2(30) DEFAULT 'TB_PET' NOT NULL,
 usuario_so VARCHAR2(100), maquina VARCHAR2(100), usuario_aplicacao VARCHAR2(100));
ALTER TABLE AUD_PET ADD CONSTRAINT ck_aud_operacao CHECK(tipo_operacao IN ('INSERT','UPDATE','DELETE'));
CREATE INDEX ix_aud_pet_data ON AUD_PET(id_registro, data_hora);
CREATE OR REPLACE VIEW CLINICA AS SELECT id id_clinica,nome,cidade,endereco,telefone FROM tb_clinica;
CREATE OR REPLACE VIEW TUTOR AS SELECT id id_tutor,nome,cpf,email,telefone FROM tb_tutor;
CREATE OR REPLACE VIEW PET AS SELECT id id_pet,id_tutor,nome,
 CASE especie WHEN 'CACHORRO' THEN 'CAO' ELSE especie END especie,raca,
 CASE sexo WHEN 'MACHO' THEN 'M' WHEN 'FEMEA' THEN 'F' END sexo,
 data_nascimento,peso_kg FROM tb_pet;
CREATE OR REPLACE VIEW ATENDIMENTO AS SELECT id id_atendimento,id_pet,id_clinica,
 id_veterinario,id_tipo_servico,veterinario,tipo_consulta,
 data_consulta data_atendimento,valor,
 CASE status WHEN 'CONCLUIDA' THEN 'REALIZADO' WHEN 'CANCELADA' THEN 'CANCELADO'
 WHEN 'AGENDADA' THEN 'AGENDADO' ELSE 'EM_ANDAMENTO' END status FROM tb_consulta;
"""
write('sql/06_evolucao_modelo.sql', extension)

json_fn = re.search(r'CREATE OR REPLACE FUNCTION FN_MONTA_JSON\b.*?END FN_MONTA_JSON;', old, re.S).group()
json_fn = json_fn.replace('CREATE OR REPLACE FUNCTION', 'FUNCTION', 1)
json_fn = json_fn[:json_fn.rfind('\nEXCEPTION')] + r"""
EXCEPTION
 WHEN e_parametro_nulo THEN RAISE_APPLICATION_ERROR(-20011,'JSON: chaves, tipos e separador obrigatorios; '||v_detalhe);
 WHEN e_qtd_divergente THEN RAISE_APPLICATION_ERROR(-20012,'JSON: listas com quantidades divergentes');
 WHEN e_tipo_invalido THEN RAISE_APPLICATION_ERROR(-20013,'JSON: tipo invalido; use S, N, B ou J');
 WHEN VALUE_ERROR THEN RAISE_APPLICATION_ERROR(-20014,'JSON: valor ou tamanho invalido para o tipo informado');
 WHEN OTHERS THEN RAISE;
END FN_MONTA_JSON;"""
# Mantem o algoritmo aprovado e completa o escape para todos os controles JSON.
json_fn = json_fn.replace('ELSE v_c', "ELSE CASE WHEN ASCII(v_c) < 32 THEN '\\u00'||TO_CHAR(ASCII(v_c),'FM0X') ELSE v_c END")
risk_fn = re.search(r'CREATE OR REPLACE FUNCTION FN_CALC_RISCO_PET\b.*?END FN_CALC_RISCO_PET;', old, re.S).group()
risk_fn = risk_fn.replace('CREATE OR REPLACE FUNCTION', 'FUNCTION', 1)
risk_fn = risk_fn.replace("    IF v_especie = 'GATO' THEN", "    IF v_especie NOT IN ('CAO','GATO') THEN\n        RAISE_APPLICATION_ERROR(-20024,'Score de sensores disponivel apenas para cao e gato');\n    END IF;\n    IF v_especie = 'GATO' THEN")
risk_fn = risk_fn[:risk_fn.rfind('\nEXCEPTION')] + r"""
EXCEPTION
 WHEN e_param_invalido THEN RAISE_APPLICATION_ERROR(-20021,'Risco: id do pet deve ser positivo');
 WHEN NO_DATA_FOUND THEN RAISE_APPLICATION_ERROR(-20022,'Risco: pet inexistente');
 WHEN ZERO_DIVIDE THEN RAISE_APPLICATION_ERROR(-20023,'Risco: pet sem leituras de sensor');
 WHEN OTHERS THEN RAISE;
END FN_CALC_RISCO_PET;"""

packages = r"""
-- Packages especializados. Sem COMMIT: a transacao pertence ao chamador Java/SQL.
CREATE OR REPLACE PACKAGE PKG_CLYVO_JSON AS
 FUNCTION FN_MONTA_JSON(p_chaves VARCHAR2,p_valores VARCHAR2,p_tipos VARCHAR2,p_sep VARCHAR2 DEFAULT '|') RETURN VARCHAR2;
 FUNCTION FN_VALOR(p_valor VARCHAR2,p_tipo VARCHAR2 DEFAULT 'S') RETURN VARCHAR2;
 FUNCTION FN_NUMERO(p_valor NUMBER) RETURN VARCHAR2;
 PROCEDURE PRC_IMPRIME_CLOB(p_texto CLOB);
END PKG_CLYVO_JSON;
/
CREATE OR REPLACE PACKAGE BODY PKG_CLYVO_JSON AS
""" + json_fn + r"""
 FUNCTION FN_VALOR(p_valor VARCHAR2,p_tipo VARCHAR2 DEFAULT 'S') RETURN VARCHAR2 IS
  v_obj VARCHAR2(32767);
 BEGIN
  -- Separador reservado, rejeitado explicitamente; nunca produz JSON silenciosamente incorreto.
  IF INSTR(p_valor,CHR(31)) > 0 THEN RAISE_APPLICATION_ERROR(-20015,'Texto contem separador reservado'); END IF;
  v_obj:=FN_MONTA_JSON('v',p_valor,p_tipo,CHR(31));
  RETURN SUBSTR(v_obj,6,LENGTH(v_obj)-6);
 END;
 FUNCTION FN_NUMERO(p_valor NUMBER) RETURN VARCHAR2 IS
 BEGIN
  RETURN FN_VALOR(TO_CHAR(p_valor,'TM9','NLS_NUMERIC_CHARACTERS=''.,'''),'N');
 END;
 PROCEDURE PRC_IMPRIME_CLOB(p_texto CLOB) IS v_pos PLS_INTEGER:=1; v_parte VARCHAR2(32767);
 BEGIN
  WHILE v_pos <= NVL(DBMS_LOB.GETLENGTH(p_texto),0) LOOP
   v_parte:=DBMS_LOB.SUBSTR(p_texto,8000,v_pos);
   DBMS_OUTPUT.PUT_LINE(v_parte); v_pos:=v_pos+LENGTH(v_parte);
  END LOOP;
 EXCEPTION WHEN OTHERS THEN RAISE;
 END;
END PKG_CLYVO_JSON;
/
CREATE OR REPLACE PACKAGE PKG_CLYVO_CLINICO AS
 FUNCTION FN_CALC_RISCO_PET(p_pet_id NUMBER) RETURN NUMBER;
 PROCEDURE PRC_CATALOGOS(p_veterinario VARCHAR2,p_tipo VARCHAR2,p_vet_id IN OUT NUMBER,p_servico_id IN OUT NUMBER);
 PROCEDURE PRC_REGISTRAR_LEITURA(p_pet NUMBER,p_dispositivo VARCHAR2,p_temperatura NUMBER,
  p_fc NUMBER,p_spo2 NUMBER,p_atividade NUMBER,p_id OUT NUMBER);
END PKG_CLYVO_CLINICO;
/
CREATE OR REPLACE PACKAGE BODY PKG_CLYVO_CLINICO AS
""" + risk_fn + r"""
 PROCEDURE PRC_CATALOGOS(p_veterinario VARCHAR2,p_tipo VARCHAR2,p_vet_id IN OUT NUMBER,p_servico_id IN OUT NUMBER) IS
  v_nome VARCHAR2(100); v_codigo VARCHAR2(30);
 BEGIN
  IF TRIM(p_veterinario) IS NULL OR p_tipo IS NULL THEN RAISE_APPLICATION_ERROR(-20025,'Veterinario e tipo obrigatorios'); END IF;
  SELECT id_veterinario INTO p_vet_id FROM VETERINARIO WHERE UPPER(TRIM(nome))=UPPER(TRIM(p_veterinario));
  IF p_servico_id IS NULL THEN
   SELECT id_tipo_servico INTO p_servico_id FROM
    (SELECT id_tipo_servico FROM TIPO_SERVICO WHERE codigo_app=p_tipo ORDER BY id_tipo_servico) WHERE ROWNUM=1;
  END IF;
  SELECT codigo_app INTO v_codigo FROM TIPO_SERVICO WHERE id_tipo_servico=p_servico_id;
  IF v_codigo<>p_tipo THEN RAISE_APPLICATION_ERROR(-20026,'Servico incompativel com o tipo da consulta'); END IF;
 EXCEPTION
  WHEN NO_DATA_FOUND THEN RAISE_APPLICATION_ERROR(-20027,'Veterinario ou servico nao cadastrado no catalogo Oracle');
  WHEN TOO_MANY_ROWS THEN RAISE_APPLICATION_ERROR(-20028,'Catalogo ambiguo; revise os cadastros');
  WHEN OTHERS THEN RAISE;
 END;
 PROCEDURE PRC_REGISTRAR_LEITURA(p_pet NUMBER,p_dispositivo VARCHAR2,p_temperatura NUMBER,
  p_fc NUMBER,p_spo2 NUMBER,p_atividade NUMBER,p_id OUT NUMBER) IS v_existe NUMBER;
 BEGIN
  IF p_pet IS NULL OR p_pet<=0 OR TRIM(p_dispositivo) IS NULL OR LENGTH(p_dispositivo)>30 THEN
   RAISE_APPLICATION_ERROR(-20029,'Pet e dispositivo validos sao obrigatorios');
  END IF;
  SELECT id INTO v_existe FROM tb_pet WHERE id=p_pet AND ativo=1;
  p_id:=SEQ_LEITURA.NEXTVAL;
  INSERT INTO LEITURA_SENSOR VALUES(p_id,p_pet,TRIM(p_dispositivo),SYSTIMESTAMP,p_temperatura,p_fc,p_spo2,p_atividade);
 EXCEPTION
  WHEN NO_DATA_FOUND THEN RAISE_APPLICATION_ERROR(-20022,'Pet inexistente ou inativo');
  WHEN VALUE_ERROR THEN RAISE_APPLICATION_ERROR(-20030,'Leitura: valor invalido');
  WHEN OTHERS THEN
   IF SQLCODE IN (-2290,-1400,-1438) THEN RAISE_APPLICATION_ERROR(-20031,'Leitura fora dos limites ou campos obrigatorios ausentes'); END IF;
   RAISE;
 END;
END PKG_CLYVO_CLINICO;
/
CREATE OR REPLACE PACKAGE PKG_CLYVO_RELATORIOS AS
 PROCEDURE PRC_ATENDIMENTOS_JSON(p_clinica_id NUMBER,p_resultado OUT CLOB);
 PROCEDURE PRC_FATURAMENTO_CLINICA(p_ano VARCHAR2,p_resultado OUT CLOB);
END PKG_CLYVO_RELATORIOS;
/
CREATE OR REPLACE PACKAGE BODY PKG_CLYVO_RELATORIOS AS
 PROCEDURE PRC_ATENDIMENTOS_JSON(p_clinica_id NUMBER,p_resultado OUT CLOB) IS
  v_existe NUMBER; v_primeiro BOOLEAN:=TRUE; v_obj VARCHAR2(32767);
  FUNCTION s(p VARCHAR2) RETURN VARCHAR2 IS BEGIN RETURN PKG_CLYVO_JSON.FN_VALOR(p); END;
  FUNCTION n(p NUMBER) RETURN VARCHAR2 IS BEGIN RETURN PKG_CLYVO_JSON.FN_NUMERO(p); END;
 BEGIN
  IF p_clinica_id IS NOT NULL THEN
   IF p_clinica_id<=0 OR p_clinica_id<>TRUNC(p_clinica_id) THEN RAISE_APPLICATION_ERROR(-20001,'Clinica deve ser um inteiro positivo'); END IF;
   SELECT id_clinica INTO v_existe FROM CLINICA WHERE id_clinica=p_clinica_id;
  END IF;
  DBMS_LOB.CREATETEMPORARY(p_resultado,TRUE);
  DBMS_LOB.WRITEAPPEND(p_resultado,1,'[');
  -- Mesmo JOIN das seis entidades aprovadas na Sprint 3.
  FOR r IN (SELECT a.*,c.nome clinica_nome,c.cidade,v.nome vet_nome,v.crmv,v.especialidade,
   ts.descricao servico_nome,p.nome pet_nome,p.especie,p.raca,p.sexo,p.peso_kg,
   t.id_tutor,t.nome tutor_nome
   FROM ATENDIMENTO a JOIN CLINICA c ON c.id_clinica=a.id_clinica
   JOIN VETERINARIO v ON v.id_veterinario=a.id_veterinario
   JOIN TIPO_SERVICO ts ON ts.id_tipo_servico=a.id_tipo_servico
   JOIN PET p ON p.id_pet=a.id_pet JOIN TUTOR t ON t.id_tutor=p.id_tutor
   WHERE p_clinica_id IS NULL OR a.id_clinica=p_clinica_id
   ORDER BY a.id_clinica,a.data_atendimento,a.id_atendimento) LOOP
   v_obj:='{"id_atendimento":'||n(r.id_atendimento)||',"data":'||s(TO_CHAR(r.data_atendimento,'YYYY-MM-DD'))||
    ',"status":'||s(r.status)||',"valor":'||n(r.valor)||
    ',"clinica":{"id":'||n(r.id_clinica)||',"nome":'||s(r.clinica_nome)||',"cidade":'||s(r.cidade)||'}'||
    ',"veterinario":{"id":'||n(r.id_veterinario)||',"nome":'||s(r.vet_nome)||',"crmv":'||s(r.crmv)||',"especialidade":'||s(r.especialidade)||'}'||
    ',"servico":{"id":'||n(r.id_tipo_servico)||',"descricao":'||s(r.servico_nome)||'}'||
    ',"pet":{"id":'||n(r.id_pet)||',"nome":'||s(r.pet_nome)||',"especie":'||s(r.especie)||
    ',"raca":'||s(r.raca)||',"sexo":'||s(r.sexo)||',"peso_kg":'||n(r.peso_kg)||'}'||
    ',"tutor":{"id":'||n(r.id_tutor)||',"nome":'||s(r.tutor_nome)||'}}';
   IF NOT v_primeiro THEN DBMS_LOB.WRITEAPPEND(p_resultado,1,','); END IF;
   DBMS_LOB.WRITEAPPEND(p_resultado,LENGTH(v_obj),v_obj); v_primeiro:=FALSE;
  END LOOP;
  DBMS_LOB.WRITEAPPEND(p_resultado,1,']');
  -- Clinica existente sem atendimentos e um resultado vazio valido: [].
 EXCEPTION
  WHEN NO_DATA_FOUND THEN RAISE_APPLICATION_ERROR(-20002,'Clinica inexistente');
  WHEN VALUE_ERROR THEN RAISE_APPLICATION_ERROR(-20004,'Falha de conversao ou tamanho no dataset');
  WHEN OTHERS THEN RAISE;
 END;
 PROCEDURE PRC_FATURAMENTO_CLINICA(p_ano VARCHAR2,p_resultado OUT CLOB) IS
  v_ano NUMBER; v_clinica NUMBER; v_servico NUMBER; v_combo NUMBER:=0; v_sub NUMBER:=0;
  v_total NUMBER:=0; v_qtd PLS_INTEGER:=0;
  FUNCTION fmt(p NUMBER) RETURN VARCHAR2 IS BEGIN RETURN TO_CHAR(p,'FM9999999999990D00','NLS_NUMERIC_CHARACTERS=''.,'''); END;
  PROCEDURE linha(p VARCHAR2) IS BEGIN p_resultado:=p_resultado||p||CHR(10); END;
  PROCEDURE detalhe IS BEGIN linha('Clinica '||v_clinica||' | Servico '||v_servico||' | '||fmt(v_combo)); END;
 BEGIN
  IF p_ano IS NULL OR NOT REGEXP_LIKE(p_ano,'^[0-9]{4}$') THEN RAISE_APPLICATION_ERROR(-20003,'Ano deve ter quatro digitos'); END IF;
  v_ano:=TO_NUMBER(p_ano);
  IF v_ano<2000 OR v_ano>2100 THEN RAISE_APPLICATION_ERROR(-20003,'Ano fora de 2000 a 2100'); END IF;
  p_resultado:=TO_CLOB('Faturamento por clinica e servico - '||p_ano||CHR(10));
  FOR r IN (SELECT id_clinica,id_tipo_servico,valor FROM ATENDIMENTO WHERE status='REALIZADO'
   AND data_atendimento>=TO_DATE(p_ano||'-01-01','YYYY-MM-DD')
   AND data_atendimento<ADD_MONTHS(TO_DATE(p_ano||'-01-01','YYYY-MM-DD'),12)
   ORDER BY id_clinica,id_tipo_servico,id_atendimento) LOOP
   IF v_qtd>0 AND (v_clinica<>r.id_clinica OR v_servico<>r.id_tipo_servico) THEN
    detalhe; v_combo:=0;
    IF v_clinica<>r.id_clinica THEN linha('Subtotal: '||fmt(v_sub)); v_sub:=0; END IF;
   END IF;
   v_clinica:=r.id_clinica; v_servico:=r.id_tipo_servico;
   v_combo:=v_combo+NVL(r.valor,0); v_sub:=v_sub+NVL(r.valor,0); v_total:=v_total+NVL(r.valor,0); v_qtd:=v_qtd+1;
  END LOOP;
  IF v_qtd>0 THEN detalhe; linha('Subtotal: '||fmt(v_sub)); END IF;
  linha('Total: '||fmt(v_total)); linha('Atendimentos realizados: '||v_qtd);
 EXCEPTION
  WHEN VALUE_ERROR OR INVALID_NUMBER THEN RAISE_APPLICATION_ERROR(-20003,'Ano invalido');
  WHEN OTHERS THEN RAISE;
 END;
END PKG_CLYVO_RELATORIOS;
/
CREATE OR REPLACE PACKAGE PKG_CLYVO_AUDITORIA AS
 FUNCTION FN_PET_JSON(p_id NUMBER,p_tutor NUMBER,p_nome VARCHAR2,p_especie VARCHAR2,p_raca VARCHAR2,
  p_sexo VARCHAR2,p_nascimento DATE,p_peso NUMBER,p_ativo NUMBER) RETURN CLOB;
 PROCEDURE PRC_AUDITAR_PET(p_id NUMBER,p_operacao VARCHAR2,p_anterior CLOB,p_novo CLOB);
END PKG_CLYVO_AUDITORIA;
/
CREATE OR REPLACE PACKAGE BODY PKG_CLYVO_AUDITORIA AS
 FUNCTION FN_PET_JSON(p_id NUMBER,p_tutor NUMBER,p_nome VARCHAR2,p_especie VARCHAR2,p_raca VARCHAR2,
  p_sexo VARCHAR2,p_nascimento DATE,p_peso NUMBER,p_ativo NUMBER) RETURN CLOB IS
  FUNCTION s(p VARCHAR2) RETURN VARCHAR2 IS BEGIN RETURN PKG_CLYVO_JSON.FN_VALOR(p); END;
  FUNCTION n(p NUMBER) RETURN VARCHAR2 IS BEGIN RETURN PKG_CLYVO_JSON.FN_NUMERO(p); END;
 BEGIN
  RETURN TO_CLOB('{"id_pet":'||n(p_id)||',"id_tutor":'||n(p_tutor)||',"nome":'||s(p_nome)||
   ',"especie":'||s(p_especie)||',"raca":'||s(p_raca)||',"sexo":'||s(p_sexo)||
   ',"data_nascimento":'||s(TO_CHAR(p_nascimento,'YYYY-MM-DD'))||',"peso_kg":'||n(p_peso)||',"ativo":'||n(p_ativo)||'}');
 END;
 PROCEDURE PRC_AUDITAR_PET(p_id NUMBER,p_operacao VARCHAR2,p_anterior CLOB,p_novo CLOB) IS
 BEGIN
  IF p_operacao IS NULL OR p_operacao NOT IN ('INSERT','UPDATE','DELETE') THEN RAISE_APPLICATION_ERROR(-20052,'Auditoria: operacao invalida'); END IF;
  INSERT INTO AUD_PET(id_registro,tipo_operacao,nome_usuario,data_hora,valor_anterior,valor_novo,
   nome_tabela,usuario_so,maquina,usuario_aplicacao)
  VALUES(p_id,p_operacao,USER,SYSTIMESTAMP,p_anterior,p_novo,'TB_PET',
   SYS_CONTEXT('USERENV','OS_USER'),SYS_CONTEXT('USERENV','HOST'),SYS_CONTEXT('USERENV','CLIENT_IDENTIFIER'));
 EXCEPTION WHEN OTHERS THEN
  IF SQLCODE=-20052 THEN RAISE; END IF;
  RAISE_APPLICATION_ERROR(-20051,'Falha ao registrar auditoria',TRUE);
 END;
END PKG_CLYVO_AUDITORIA;
/
-- Fachada: contrato JDBC ja utilizado pelo Java da Sprint 4.
CREATE OR REPLACE PACKAGE PKG_CLYVOVET AS
 PROCEDURE PRC_ATENDIMENTOS_JSON(p_clinica_id NUMBER,p_resultado OUT CLOB);
 PROCEDURE PRC_FATURAMENTO_CLINICA(p_ano VARCHAR2,p_resultado OUT CLOB);
 FUNCTION FN_CALC_RISCO_PET(p_pet_id NUMBER) RETURN NUMBER;
 PROCEDURE PRC_REGISTRAR_LEITURA(p_pet NUMBER,p_dispositivo VARCHAR2,p_temperatura NUMBER,
  p_fc NUMBER,p_spo2 NUMBER,p_atividade NUMBER,p_id OUT NUMBER);
END PKG_CLYVOVET;
/
CREATE OR REPLACE PACKAGE BODY PKG_CLYVOVET AS
 PROCEDURE PRC_ATENDIMENTOS_JSON(p_clinica_id NUMBER,p_resultado OUT CLOB) IS
 BEGIN PKG_CLYVO_RELATORIOS.PRC_ATENDIMENTOS_JSON(p_clinica_id,p_resultado); END;
 PROCEDURE PRC_FATURAMENTO_CLINICA(p_ano VARCHAR2,p_resultado OUT CLOB) IS
 BEGIN PKG_CLYVO_RELATORIOS.PRC_FATURAMENTO_CLINICA(p_ano,p_resultado); END;
 FUNCTION FN_CALC_RISCO_PET(p_pet_id NUMBER) RETURN NUMBER IS
 BEGIN RETURN PKG_CLYVO_CLINICO.FN_CALC_RISCO_PET(p_pet_id); END;
 PROCEDURE PRC_REGISTRAR_LEITURA(p_pet NUMBER,p_dispositivo VARCHAR2,p_temperatura NUMBER,
  p_fc NUMBER,p_spo2 NUMBER,p_atividade NUMBER,p_id OUT NUMBER) IS
 BEGIN PKG_CLYVO_CLINICO.PRC_REGISTRAR_LEITURA(p_pet,p_dispositivo,p_temperatura,p_fc,p_spo2,p_atividade,p_id); END;
END PKG_CLYVOVET;
/
-- Trigger fino: identifica o evento e repassa os escalares OLD/NEW ao package.
CREATE OR REPLACE TRIGGER TRG_AUD_PET AFTER INSERT OR UPDATE OR DELETE ON tb_pet FOR EACH ROW
DECLARE v_op VARCHAR2(10); v_old CLOB; v_new CLOB;
BEGIN
 IF INSERTING THEN v_op:='INSERT'; ELSIF UPDATING THEN v_op:='UPDATE'; ELSE v_op:='DELETE'; END IF;
 IF UPDATING OR DELETING THEN v_old:=PKG_CLYVO_AUDITORIA.FN_PET_JSON(:OLD.id,:OLD.id_tutor,:OLD.nome,
  :OLD.especie,:OLD.raca,:OLD.sexo,:OLD.data_nascimento,:OLD.peso_kg,:OLD.ativo); END IF;
 IF INSERTING OR UPDATING THEN v_new:=PKG_CLYVO_AUDITORIA.FN_PET_JSON(:NEW.id,:NEW.id_tutor,:NEW.nome,
  :NEW.especie,:NEW.raca,:NEW.sexo,:NEW.data_nascimento,:NEW.peso_kg,:NEW.ativo); END IF;
 PKG_CLYVO_AUDITORIA.PRC_AUDITAR_PET(NVL(:NEW.id,:OLD.id),v_op,v_old,v_new);
END;
/
-- Catalogos sao FKs reais. Campos textuais permanecem para compatibilidade JPA.
CREATE OR REPLACE TRIGGER TRG_CONSULTA_CATALOGOS
BEFORE INSERT OR UPDATE OF veterinario,tipo_consulta,id_veterinario,id_tipo_servico ON tb_consulta FOR EACH ROW
DECLARE v_vet NUMBER; v_serv NUMBER;
BEGIN
 v_vet:=:NEW.id_veterinario; v_serv:=:NEW.id_tipo_servico;
 IF UPDATING AND :NEW.tipo_consulta<>:OLD.tipo_consulta THEN v_serv:=NULL; END IF;
 PKG_CLYVO_CLINICO.PRC_CATALOGOS(:NEW.veterinario,:NEW.tipo_consulta,v_vet,v_serv);
 :NEW.id_veterinario:=v_vet; :NEW.id_tipo_servico:=v_serv;
END;
/
"""
write('sql/07_packages_gatilhos.sql', packages)

# Copia exatamente as migrations preexistentes; nenhuma checksum e reescrita.
for i, name in enumerate(['V1__estrutura.sql','V2__constraints.sql','V3__perfis.sql','V4__cancelamento.sql','V5__integracao_database.sql'],1):
    shutil.copyfile(ORACLE / name, ROOT / 'sql' / f'0{i}_{name.split("__")[1]}')
(ORACLE / 'V6__continuidade_modelo.sql').write_text(extension.strip()+'\n',encoding='utf-8')
(ORACLE / 'V7__packages_sprint4.sql').write_text(packages.strip()+'\n',encoding='utf-8')

catalogs=[]
for stmt in re.findall(r'INSERT INTO VETERINARIO\b.*?;',old,re.S): catalogs.append(stmt)
for i,desc,price,code in [(1,'Consulta clinica',180,'ROTINA'),(2,'Vacinacao',120,'VACINACAO'),(3,'Exames laboratoriais',250,'EXAME'),(4,'Cirurgia',1500,'CIRURGIA'),(5,'Ultrassonografia',320,'EXAME'),(6,'Retorno',90,'RETORNO'),(7,'Consulta preventiva',180,'PREVENTIVA'),(8,'Emergencia',350,'EMERGENCIA')]:
    catalogs.append(f"INSERT INTO TIPO_SERVICO VALUES({i},'{desc}',{price},'{code}');")
write('sql/08_catalogos.sql','-- Carga de catalogos ficticios aprovada/adaptada. Executar uma vez.\n'+'\n'.join(catalogs)+'\nCOMMIT;')

# Reutiliza as MESMAS linhas da carga aprovada, convertendo somente o mapeamento fisico.
seed=['-- Carga ficticia derivada da Sprint 3. Executar uma vez apos 08_catalogos.sql.']
for i in range(1,7):
    match=re.search(rf"INSERT INTO CLINICA .*?VALUES \({i},\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)'\);",old)
    name,city,bairro,phone=match.groups()
    seed.append(f"INSERT INTO tb_clinica(id,nome,cnpj,telefone,email,endereco,cidade,estado,ativo) VALUES({i},'{name}','{i:014d}','113000{i:04d}','clinica{i}@example.test','Rua de demonstracao, {i} - {bairro}','{city}','SP',1);")
for i in range(1,9):
    match=re.search(rf"INSERT INTO TUTOR .*?VALUES \({i},\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)'\);",old)
    name,cpf,email,phone,city=match.groups()
    cpf=re.sub(r'\D','',cpf); phone=re.sub(r'\D','',phone)
    seed.append(f"INSERT INTO tb_tutor(id,nome,cpf,email,telefone,data_nascimento,ativo) VALUES({i},'{name}','{cpf}','tutor{i}@example.test','{phone}',DATE '1990-01-01',1);")
pet_statements=re.findall(r'INSERT INTO PET\b.*?;',old,re.S)[:10]
for stmt in pet_statements:
    stmt=stmt.replace('INSERT INTO PET (id_pet,','INSERT INTO tb_pet (id,').replace("'CAO'","'CACHORRO'").replace("'M'","'MACHO'").replace("'F'","'FEMEA'")
    seed.append(stmt)
for stmt in re.findall(r'INSERT INTO ATENDIMENTO\b.*?;',old,re.S):
    vals=re.search(r'VALUES\s*\((.*)\);',stmt,re.S).group(1)
    # Todos os primeiros cinco valores sao IDs numericos, os demais mantem data/valor/status.
    parts=vals.split(',',5); aid,pet,vet,clinic,service=[int(x.strip()) for x in parts[:5]]
    tail=parts[5].strip(); code={1:'ROTINA',2:'VACINACAO',3:'EXAME',4:'CIRURGIA',5:'EXAME'}[service]
    vetname=re.search(rf"VALUES\s*\({vet},\s*'([^']*)'",'\n'.join(catalogs)).group(1)
    tail=tail.replace("'REALIZADO'","'CONCLUIDA'").replace("'AGENDADO'","'AGENDADA'").replace("'CANCELADO'","'CANCELADA'")
    # data, valor, status sao colocados depois do nome e tipo da aplicacao.
    seed.append(f"INSERT INTO tb_consulta(id,id_pet,id_clinica,id_veterinario,id_tipo_servico,veterinario,tipo_consulta,data_consulta,valor,status,criado_em) VALUES({aid},{pet},{clinic},{vet},{service},'{vetname}','{code}',{tail},SYSTIMESTAMP);")
seed.extend(re.findall(r'INSERT INTO LEITURA_SENSOR\b.*?;',old,re.S))
seed.append('COMMIT;')
for table in ['tb_clinica','tb_tutor','tb_pet','tb_consulta']:
    seed.append(f'ALTER TABLE {table} MODIFY id GENERATED BY DEFAULT AS IDENTITY (START WITH LIMIT VALUE);')
write('sql/09_dados_demonstracao.sql','\n'.join(seed))

header="""-- FIAP | 2TDSPF | ClyvoVet | Sprint 4 | Entrega 04/11/2026
-- Carlos Alberto Guedes Neto RM 566022; Eduardo Novaes Mollo RM 561515;
-- Luan Peixoto Marins Rocha RM 562258; Mathaus Victor Souza Marcelino RM 564146;
-- Vinicius Luis Exposito Morassi RM 563340.
-- INSTALACAO MANUAL EM SCHEMA SEM OS OBJETOS CLYVOVET. NAO EXECUTAR SOBRE SPRINT 3.
-- Alternativa ao Flyway. Nao misturar os dois instaladores no mesmo schema.
SET DEFINE OFF
SET SERVEROUTPUT ON SIZE UNLIMITED
WHENEVER SQLERROR EXIT SQL.SQLCODE ROLLBACK
DECLARE v_qtd NUMBER;
BEGIN
 SELECT COUNT(*) INTO v_qtd FROM user_objects WHERE object_name IN
 ('PET','CLINICA','TUTOR','ATENDIMENTO','TB_PET','TB_CLINICA','TB_TUTOR','VETERINARIO','TIPO_SERVICO','LEITURA_SENSOR','AUD_PET','PKG_CLYVOVET');
 IF v_qtd>0 THEN RAISE_APPLICATION_ERROR(-20901,'Schema com objetos ClyvoVet: instalacao interrompida para preservar dados. Use configuracao de schema dedicado.'); END IF;
END;
/
"""
combined=header+'\n'.join((ROOT/'sql'/name).read_text(encoding='utf-8') for name in ['01_estrutura.sql','02_constraints.sql','03_perfis.sql','04_cancelamento.sql','05_integracao_database.sql','06_evolucao_modelo.sql','07_packages_gatilhos.sql'])
combined+='\n-- Instale os catalogos e dados separadamente, quando desejar a demonstracao.\n'
write('sql/2TDSPF_2026_CodigoSql_Integrantes.sql',combined)
write('sql/10_verificar_objetos.sql',r"""
SET SERVEROUTPUT ON
-- A sincronizacao IDENTITY da carga pode invalidar dependentes. Recompilar
-- os objetos deste projeto antes de exibir e verificar o status final.
ALTER PACKAGE PKG_CLYVO_JSON COMPILE BODY;
ALTER PACKAGE PKG_CLYVO_CLINICO COMPILE BODY;
ALTER PACKAGE PKG_CLYVO_RELATORIOS COMPILE BODY;
ALTER PACKAGE PKG_CLYVO_AUDITORIA COMPILE BODY;
ALTER PACKAGE PKG_CLYVOVET COMPILE BODY;
ALTER TRIGGER TRG_AUD_PET COMPILE;
ALTER TRIGGER TRG_CONSULTA_CATALOGOS COMPILE;
SELECT object_type,object_name,status FROM user_objects
 WHERE object_name LIKE 'PKG_CLYVO%' OR object_name IN ('TRG_AUD_PET','TRG_CONSULTA_CATALOGOS') ORDER BY object_name,object_type;
SELECT name,type,line,position,text FROM user_errors WHERE name LIKE 'PKG_CLYVO%' OR name IN ('TRG_AUD_PET','TRG_CONSULTA_CATALOGOS');
DECLARE v_erros NUMBER; v_pendentes NUMBER; v_invalidos NUMBER; v_objetos NUMBER;
BEGIN
 SELECT COUNT(*) INTO v_erros FROM user_errors WHERE name LIKE 'PKG_CLYVO%' OR name IN ('TRG_AUD_PET','TRG_CONSULTA_CATALOGOS');
 IF v_erros>0 THEN RAISE_APPLICATION_ERROR(-20902,'Objetos com erros de compilacao'); END IF;
 SELECT COUNT(*),COUNT(CASE WHEN status<>'VALID' THEN 1 END) INTO v_objetos,v_invalidos
 FROM user_objects WHERE object_name IN ('PKG_CLYVO_JSON','PKG_CLYVO_CLINICO','PKG_CLYVO_RELATORIOS',
 'PKG_CLYVO_AUDITORIA','PKG_CLYVOVET','TRG_AUD_PET','TRG_CONSULTA_CATALOGOS');
 IF v_objetos<>12 OR v_invalidos>0 THEN RAISE_APPLICATION_ERROR(-20902,'Objetos ausentes ou INVALID apos recompilacao'); END IF;
 SELECT COUNT(*) INTO v_pendentes FROM tb_consulta WHERE id_veterinario IS NULL OR id_tipo_servico IS NULL;
 IF v_pendentes>0 THEN RAISE_APPLICATION_ERROR(-20903,'Consultas antigas sem catalogos: fazer conciliacao antes da exportacao'); END IF;
 DBMS_OUTPUT.PUT_LINE('Compilacao e catalogos consistentes.');
END;
/
SELECT 'TB_PET' tabela,COUNT(*) quantidade FROM tb_pet UNION ALL SELECT 'PET (view)',COUNT(*) FROM PET
UNION ALL SELECT 'TB_CONSULTA',COUNT(*) FROM tb_consulta UNION ALL SELECT 'ATENDIMENTO (view)',COUNT(*) FROM ATENDIMENTO;
SELECT id_auditoria,id_registro,tipo_operacao,nome_usuario,data_hora FROM AUD_PET ORDER BY id_auditoria;
""")

write('sql/11_testes_transacionais.sql',r"""
-- Execute em base demonstrativa depois de 08 e 09. DML do teste sofre ROLLBACK.
SET SERVEROUTPUT ON SIZE UNLIMITED
DECLARE
 v_json CLOB; v_rel CLOB; v_id NUMBER; v_peso NUMBER; v_aud NUMBER; v_score NUMBER;
 PROCEDURE exigir(p BOOLEAN,p_msg VARCHAR2) IS BEGIN IF p IS NULL OR NOT p THEN RAISE_APPLICATION_ERROR(-20990,p_msg); END IF; END;
 PROCEDURE esperar_erro(p_bloco VARCHAR2,p_codigo NUMBER) IS v_ocorreu BOOLEAN:=FALSE;
 BEGIN
  BEGIN EXECUTE IMMEDIATE p_bloco;
  EXCEPTION WHEN OTHERS THEN
   IF SQLCODE<>p_codigo THEN RAISE; END IF;
   v_ocorreu:=TRUE; DBMS_OUTPUT.PUT_LINE('Excecao esperada: '||p_codigo);
  END;
  exigir(v_ocorreu,'Excecao esperada nao ocorreu: '||p_codigo);
 END;
BEGIN
 SAVEPOINT teste_sprint4;
 exigir(PKG_CLYVO_JSON.FN_VALOR('Rex "Junior" | Sao Paulo')='"Rex \"Junior\" | Sao Paulo"','Escape JSON incorreto');
 esperar_erro('DECLARE x VARCHAR2(32767); BEGIN x:=PKG_CLYVO_JSON.FN_MONTA_JSON(''a|b'',''1'',''N|N''); END;',-20012);
 esperar_erro('DECLARE x NUMBER; BEGIN x:=PKG_CLYVOVET.FN_CALC_RISCO_PET(-1); END;',-20021);
 esperar_erro('DECLARE x NUMBER; BEGIN x:=PKG_CLYVOVET.FN_CALC_RISCO_PET(999999); END;',-20022);
 esperar_erro('DECLARE x NUMBER; BEGIN x:=PKG_CLYVOVET.FN_CALC_RISCO_PET(10); END;',-20023);
 esperar_erro('DECLARE x CLOB; BEGIN PKG_CLYVOVET.PRC_ATENDIMENTOS_JSON(-1,x); END;',-20001);
 esperar_erro('DECLARE x CLOB; BEGIN PKG_CLYVOVET.PRC_ATENDIMENTOS_JSON(999999,x); END;',-20002);
 esperar_erro('DECLARE x CLOB; BEGIN PKG_CLYVOVET.PRC_FATURAMENTO_CLINICA(''ABC'',x); END;',-20003);
 PKG_CLYVOVET.PRC_ATENDIMENTOS_JSON(NULL,v_json);
 exigir(DBMS_LOB.SUBSTR(v_json,1,1)='[','Dataset deve ser array');
 PKG_CLYVOVET.PRC_FATURAMENTO_CLINICA('2026',v_rel);
 exigir(DBMS_LOB.INSTR(v_rel,'Total: 15635.00')>0,'Faturamento divergente da carga aprovada');
 v_score:=PKG_CLYVOVET.FN_CALC_RISCO_PET(1);
 exigir(v_score BETWEEN 0 AND 100,'Risco fora de 0 a 100');
 PKG_CLYVOVET.PRC_REGISTRAR_LEITURA(1,'ESP32-TESTE',38.5,90,98,60,v_id);
 SELECT peso_kg INTO v_peso FROM tb_pet WHERE id=1;
 SELECT COUNT(*) INTO v_aud FROM AUD_PET WHERE id_registro=1;
 UPDATE tb_pet SET peso_kg=v_peso+0.1 WHERE id=1;
 DECLARE v_depois NUMBER; BEGIN
  SELECT COUNT(*) INTO v_depois FROM AUD_PET WHERE id_registro=1;
  exigir(v_depois=v_aud+1,'Trigger nao auditou UPDATE');
 END;
 INSERT INTO tb_pet(nome,especie,raca,data_nascimento,peso_kg,sexo,ativo,id_tutor)
 VALUES('Pet teste transacional','CACHORRO','SRD',DATE '2024-01-01',10,'MACHO',1,1) RETURNING id INTO v_id;
 DELETE FROM tb_pet WHERE id=v_id;
 DECLARE v_total NUMBER; BEGIN
  SELECT COUNT(*) INTO v_total FROM AUD_PET WHERE id_registro=v_id;
  exigir(v_total=2,'Auditoria INSERT e DELETE ausente');
 END;
 ROLLBACK TO teste_sprint4;
 DBMS_OUTPUT.PUT_LINE('Testes concluidos; DML de teste revertido.');
EXCEPTION WHEN OTHERS THEN ROLLBACK TO teste_sprint4; RAISE;
END;
/
""")

write('.gitignore',"""
.env
.env.*
!.env.example
data/
evidencias/*.log
tools/__pycache__/
entrega/
""")
write('.env.example',"""
# Exemplo. Configure localmente; nao versionar senha.
DB_URL=jdbc:oracle:thin:@//HOST:1521/SERVICE_NAME
DB_USERNAME=USUARIO_FIAP
DB_PASSWORD=
ADMIN_USERNAME=admin
ADMIN_PASSWORD=
""")
# A FIAP normalmente fornece um unico schema por aluno. Prefixos CV4 preservam
# os objetos da Sprint 3 nesse mesmo schema sem exigir CREATE USER ou DROP.
names = {'CLINICA':'CV4_CLINICA','TUTOR':'CV4_TUTOR','PET':'CV4_PET',
 'ATENDIMENTO':'CV4_ATENDIMENTO','VETERINARIO':'CV4_VETERINARIO',
 'TIPO_SERVICO':'CV4_TIPO_SERVICO','LEITURA_SENSOR':'CV4_LEITURA_SENSOR',
 'AUD_PET':'CV4_AUD_PET','SEQ_VETERINARIO':'CV4_SEQ_VETERINARIO',
 'SEQ_LEITURA':'CV4_SEQ_LEITURA','TRG_AUD_PET':'TRG_CV4_AUD_PET',
 'TRG_CONSULTA_CATALOGOS':'TRG_CV4_CONSULTA_CAT',
 'pk_veterinario':'pk_cv4_veterinario','uk_veterinario_crmv':'uk_cv4_vet_crmv',
 'pk_tipo_servico':'pk_cv4_tipo_servico','ck_tipo_servico_preco':'ck_cv4_servico_preco',
 'pk_leitura':'pk_cv4_leitura','fk_leitura_pet':'fk_cv4_leitura_pet'}
def namespace(text):
    for before,after in names.items():
        text=re.sub(r'\b'+re.escape(before)+r'\b',after,text)
    # Constraints e indices tambem pertencem ao schema, nao apenas a tabela.
    # Evita colidir com fk_pet_tutor, por exemplo, da Sprint 3.
    text=re.sub(r'(\bCONSTRAINT\s+)(\w+)',lambda m:m[1]+('CV4_'+m[2] if not m[2].upper().startswith('CV4_') else m[2]),text,flags=re.I)
    text=re.sub(r'(\bCREATE\s+(?:UNIQUE\s+)?INDEX\s+)(\w+)',lambda m:m[1]+('CV4_'+m[2] if not m[2].upper().startswith('CV4_') else m[2]),text,flags=re.I)
    return text
audit_base="""CREATE TABLE AUD_PET (
 id_auditoria NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
 id_registro NUMBER(19),tipo_operacao VARCHAR2(10) NOT NULL,
 nome_usuario VARCHAR2(128) NOT NULL,data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
 valor_anterior CLOB,valor_novo CLOB);
"""
write('sql/05_integracao_database.sql',audit_base)
for path in (ROOT/'sql').glob('*.sql'):
    if path.name=='2TDSPF_2026_CodigoSql_Integrantes.sql': continue
    path.write_text(namespace(path.read_text(encoding='utf-8')),encoding='utf-8')
# Objetos antigos ficam intocados. Detecta exclusivamente os nomes desta aplicacao.
header=namespace(header)
header=header.replace("('CV4_PET','CV4_CLINICA','CV4_TUTOR','CV4_ATENDIMENTO'", "('CV4_PET','CV4_CLINICA','CV4_TUTOR','CV4_ATENDIMENTO'")
combined=header+'\n'.join((ROOT/'sql'/name).read_text(encoding='utf-8') for name in
 ['01_estrutura.sql','02_constraints.sql','03_perfis.sql','04_cancelamento.sql',
  '05_integracao_database.sql','06_evolucao_modelo.sql','07_packages_gatilhos.sql','08_catalogos.sql'])
write('sql/2TDSPF_2026_CodigoSql_Integrantes.sql',combined)
new_migrations=JAVA/'src/main/resources/db/oracle-sprint4'
new_migrations.mkdir(exist_ok=True)
for name in ['V1__estrutura.sql','V2__constraints.sql','V3__perfis.sql','V4__cancelamento.sql']:
    (new_migrations/name).write_text(namespace((ORACLE/name).read_text(encoding='utf-8')),encoding='utf-8')
(new_migrations/'V5__continuidade_database.sql').write_text(namespace(audit_base+extension+packages),encoding='utf-8')
(new_migrations/'V6__catalogos.sql').write_text(namespace('\n'.join(catalogs)),encoding='utf-8')
# Remove apenas os dois arquivos gerados anteriormente por este programa.
for name in ['V6__continuidade_modelo.sql','V7__packages_sprint4.sql']:
    (ORACLE/name).unlink(missing_ok=True)
print('Scripts gerados; nenhuma conexao remota realizada.')
