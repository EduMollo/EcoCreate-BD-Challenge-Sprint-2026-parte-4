-- Packages especializados. Sem COMMIT: a transacao pertence ao chamador Java/SQL.
CREATE OR REPLACE PACKAGE PKG_CLYVO_JSON AS
 FUNCTION FN_MONTA_JSON(p_chaves VARCHAR2,p_valores VARCHAR2,p_tipos VARCHAR2,p_sep VARCHAR2 DEFAULT '|') RETURN VARCHAR2;
 FUNCTION FN_VALOR(p_valor VARCHAR2,p_tipo VARCHAR2 DEFAULT 'S') RETURN VARCHAR2;
 FUNCTION FN_NUMERO(p_valor NUMBER) RETURN VARCHAR2;
 PROCEDURE PRC_IMPRIME_CLOB(p_texto CLOB);
END PKG_CLYVO_JSON;
/
CREATE OR REPLACE PACKAGE BODY PKG_CLYVO_JSON AS
FUNCTION FN_MONTA_JSON (
    p_chaves   IN VARCHAR2,               -- ex.: 'id|nome|peso_kg'
    p_valores  IN VARCHAR2,               -- ex.: '1|Rex|32.5'
    p_tipos    IN VARCHAR2,               -- ex.: 'N|S|N'
    p_sep      IN VARCHAR2 DEFAULT '|'    -- separador das listas
) RETURN VARCHAR2
IS
    -- excecoes proprias -----------------------------------------------------------
    e_parametro_nulo    EXCEPTION;   -- lista obrigatoria vazia ou chave em branco
    e_qtd_divergente    EXCEPTION;   -- listas com quantidades diferentes de itens
    e_tipo_invalido     EXCEPTION;   -- tipo fora de S / N / B / J

    -- variaveis de trabalho -------------------------------------------------------
    v_qtd_chaves   PLS_INTEGER;
    v_qtd_valores  PLS_INTEGER;
    v_qtd_tipos    PLS_INTEGER;
    v_chave        VARCHAR2(4000);
    v_valor        VARCHAR2(4000);
    v_tipo         VARCHAR2(10);
    v_detalhe      VARCHAR2(400);    -- complemento da mensagem de erro
    v_json         VARCHAR2(32767);

    -- Conta os itens de uma lista delimitada: numero de separadores + 1.
    FUNCTION contar_itens(p_lista VARCHAR2) RETURN PLS_INTEGER IS
        v_qtd PLS_INTEGER := 1;
        v_pos PLS_INTEGER := 1;
    BEGIN
        IF p_lista IS NULL THEN
            RETURN 1;                              -- lista vazia = um unico item nulo
        END IF;
        LOOP
            v_pos := INSTR(p_lista, p_sep, v_pos);
            EXIT WHEN NVL(v_pos, 0) = 0;
            v_qtd := v_qtd + 1;
            v_pos := v_pos + LENGTH(p_sep);
        END LOOP;
        RETURN v_qtd;
    END contar_itens;

    -- Devolve o i-esimo item da lista (item vazio => NULL).
    FUNCTION item(p_lista VARCHAR2, p_i PLS_INTEGER) RETURN VARCHAR2 IS
        v_ini PLS_INTEGER;
        v_fim PLS_INTEGER;
    BEGIN
        IF p_lista IS NULL THEN
            RETURN NULL;
        END IF;
        IF p_i = 1 THEN
            v_ini := 1;
        ELSE
            v_ini := INSTR(p_lista, p_sep, 1, p_i - 1) + LENGTH(p_sep);
        END IF;
        v_fim := INSTR(p_lista, p_sep, 1, p_i);    -- separador seguinte (0 = ultimo item)
        IF v_fim = 0 THEN
            RETURN SUBSTR(p_lista, v_ini);
        END IF;
        RETURN SUBSTR(p_lista, v_ini, v_fim - v_ini);
    END item;

    -- Escapa, caractere a caractere, o que nao pode aparecer cru dentro de aspas JSON.
    FUNCTION escapar(p_txt VARCHAR2) RETURN VARCHAR2 IS
        v_out VARCHAR2(32767);
        v_c   VARCHAR2(4);
    BEGIN
        FOR i IN 1 .. NVL(LENGTH(p_txt), 0) LOOP
            v_c := SUBSTR(p_txt, i, 1);
            v_out := v_out ||
                CASE v_c
                    WHEN '\'     THEN '\\'
                    WHEN '"'     THEN '\"'
                    WHEN CHR(10) THEN '\n'
                    WHEN CHR(13) THEN '\r'
                    WHEN CHR(9)  THEN '\t'
                    WHEN CHR(8)  THEN '\b'
                    WHEN CHR(12) THEN '\f'
                    ELSE CASE WHEN ASCII(v_c) < 32 THEN '\u00'||TO_CHAR(ASCII(v_c),'FM0X') ELSE v_c END
                END;
        END LOOP;
        RETURN v_out;
    END escapar;

    -- Valida e normaliza um numero para o padrao JSON: sinal opcional, digitos e no
    -- maximo um ponto decimal. Aceita virgula na entrada. Levanta VALUE_ERROR se invalido.
    FUNCTION numero_json(p_txt VARCHAR2) RETURN VARCHAR2 IS
        v_txt     VARCHAR2(100) := REPLACE(TRIM(p_txt), ',', '.');
        v_sinal   VARCHAR2(1)   := '';
        v_c       VARCHAR2(1);
        v_pontos  PLS_INTEGER := 0;
        v_digitos PLS_INTEGER := 0;
    BEGIN
        IF SUBSTR(v_txt, 1, 1) IN ('-', '+') THEN
            IF SUBSTR(v_txt, 1, 1) = '-' THEN
                v_sinal := '-';
            END IF;
            v_txt := SUBSTR(v_txt, 2);
        END IF;
        FOR i IN 1 .. NVL(LENGTH(v_txt), 0) LOOP
            v_c := SUBSTR(v_txt, i, 1);
            IF v_c BETWEEN '0' AND '9' THEN
                v_digitos := v_digitos + 1;
            ELSIF v_c = '.' THEN
                v_pontos := v_pontos + 1;
            ELSE
                RAISE VALUE_ERROR;                 -- caractere que nao pertence a um numero
            END IF;
        END LOOP;
        IF v_digitos = 0 OR v_pontos > 1 THEN
            RAISE VALUE_ERROR;
        END IF;
        -- JSON nao aceita ".5", "5." nem zeros a esquerda ("007")
        IF SUBSTR(v_txt, 1, 1) = '.' THEN
            v_txt := '0' || v_txt;
        END IF;
        IF SUBSTR(v_txt, -1) = '.' THEN
            v_txt := SUBSTR(v_txt, 1, LENGTH(v_txt) - 1);
        END IF;
        WHILE LENGTH(v_txt) > 1 AND SUBSTR(v_txt, 1, 1) = '0' AND SUBSTR(v_txt, 2, 1) <> '.' LOOP
            v_txt := SUBSTR(v_txt, 2);
        END LOOP;
        RETURN v_sinal || v_txt;
    END numero_json;

    -- Converte representacoes usuais de booleano para true/false.
    FUNCTION booleano_json(p_txt VARCHAR2) RETURN VARCHAR2 IS
        v_txt VARCHAR2(20) := UPPER(TRIM(p_txt));
    BEGIN
        IF v_txt IN ('S', 'SIM', 'TRUE', 'T', 'V', '1') THEN
            RETURN 'true';
        ELSIF v_txt IN ('N', 'NAO', 'FALSE', 'F', '0') THEN
            RETURN 'false';
        END IF;
        RAISE VALUE_ERROR;
    END booleano_json;

BEGIN
    -- 1) validacao dos parametros
    IF p_chaves IS NULL OR p_tipos IS NULL OR p_sep IS NULL THEN
        v_detalhe := 'as listas de chaves e de tipos e o separador sao obrigatorios';
        RAISE e_parametro_nulo;
    END IF;

    v_qtd_chaves  := contar_itens(p_chaves);
    v_qtd_valores := contar_itens(p_valores);
    v_qtd_tipos   := contar_itens(p_tipos);

    IF v_qtd_chaves <> v_qtd_valores OR v_qtd_chaves <> v_qtd_tipos THEN
        RAISE e_qtd_divergente;
    END IF;

    -- 2) montagem do objeto, par a par
    v_json := '{';
    FOR i IN 1 .. v_qtd_chaves LOOP
        v_chave := TRIM(item(p_chaves, i));
        v_valor := item(p_valores, i);
        v_tipo  := UPPER(TRIM(item(p_tipos, i)));

        IF v_chave IS NULL THEN
            v_detalhe := 'chave em branco na posicao ' || i;
            RAISE e_parametro_nulo;
        END IF;
        IF v_tipo IS NULL OR v_tipo NOT IN ('S', 'N', 'B', 'J') THEN
            RAISE e_tipo_invalido;
        END IF;

        IF i > 1 THEN
            v_json := v_json || ',';
        END IF;
        v_json := v_json || '"' || escapar(v_chave) || '":';

        IF v_valor IS NULL THEN
            v_json := v_json || 'null';
        ELSIF v_tipo = 'S' THEN
            v_json := v_json || '"' || escapar(v_valor) || '"';
        ELSIF v_tipo = 'N' THEN
            v_json := v_json || numero_json(v_valor);
        ELSIF v_tipo = 'B' THEN
            v_json := v_json || booleano_json(v_valor);
        ELSE                                       -- 'J': JSON pronto (objeto/array aninhado)
            v_json := v_json || v_valor;
        END IF;
    END LOOP;
    v_json := v_json || '}';

    RETURN v_json;

EXCEPTION
 WHEN e_parametro_nulo THEN RAISE_APPLICATION_ERROR(-20011,'JSON: chaves, tipos e separador obrigatorios; '||v_detalhe);
 WHEN e_qtd_divergente THEN RAISE_APPLICATION_ERROR(-20012,'JSON: listas com quantidades divergentes');
 WHEN e_tipo_invalido THEN RAISE_APPLICATION_ERROR(-20013,'JSON: tipo invalido; use S, N, B ou J');
 WHEN VALUE_ERROR THEN RAISE_APPLICATION_ERROR(-20014,'JSON: valor ou tamanho invalido para o tipo informado');
 WHEN OTHERS THEN RAISE;
END FN_MONTA_JSON;
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
FUNCTION FN_CALC_RISCO_PET (p_pet_id IN NUMBER) RETURN NUMBER
IS
    e_param_invalido  EXCEPTION;              -- id nulo ou nao positivo

    v_nome        CV4_PET.nome%TYPE;
    v_especie     CV4_PET.especie%TYPE;

    -- acumuladores (somatorio manual)
    v_qtd         PLS_INTEGER := 0;
    v_soma_temp   NUMBER := 0;
    v_soma_fc     NUMBER := 0;
    v_soma_spo2   NUMBER := 0;
    v_soma_ativ   NUMBER := 0;

    -- medias
    v_med_temp    NUMBER;
    v_med_fc      NUMBER;
    v_med_spo2    NUMBER;
    v_med_ativ    NUMBER;

    -- faixas de referencia por especie
    v_temp_min    NUMBER;
    v_temp_max    NUMBER;
    v_fc_min      NUMBER;
    v_fc_max      NUMBER;
    v_spo2_min    NUMBER := 95;
    v_ativ_min    NUMBER;

    -- sub-scores e resultado
    v_sub_temp    NUMBER;
    v_sub_fc      NUMBER;
    v_sub_spo2    NUMBER;
    v_sub_ativ    NUMBER;
    v_score       NUMBER;

    -- Sub-score 0..100: distancia da media ate a faixa normal x fator de sensibilidade.
    FUNCTION sub_score(p_media NUMBER, p_min NUMBER, p_max NUMBER, p_fator NUMBER) RETURN NUMBER IS
        v_desvio NUMBER := 0;
    BEGIN
        IF p_media < p_min THEN
            v_desvio := p_min - p_media;
        ELSIF p_max IS NOT NULL AND p_media > p_max THEN
            v_desvio := p_media - p_max;
        END IF;
        RETURN LEAST(100, v_desvio * p_fator);
    END sub_score;

    FUNCTION classificar(p_score NUMBER) RETURN VARCHAR2 IS
    BEGIN
        IF    p_score < 25 THEN RETURN 'BAIXO';
        ELSIF p_score < 50 THEN RETURN 'MODERADO';
        ELSIF p_score < 75 THEN RETURN 'ALTO';
        ELSE                    RETURN 'CRITICO';
        END IF;
    END classificar;

    FUNCTION fmt(p_num NUMBER) RETURN VARCHAR2 IS
    BEGIN
        RETURN TO_CHAR(p_num, 'FM9990.0', 'NLS_NUMERIC_CHARACTERS=''.,''');
    END fmt;

BEGIN
    -- 1) validacao do parametro
    IF p_pet_id IS NULL OR p_pet_id <= 0 THEN
        RAISE e_param_invalido;
    END IF;

    -- 2) especie define a faixa de referencia (NO_DATA_FOUND se o pet nao existir)
    SELECT nome, especie
      INTO v_nome, v_especie
      FROM CV4_PET
     WHERE id_pet = p_pet_id;

    IF v_especie NOT IN ('CAO','GATO') THEN
        RAISE_APPLICATION_ERROR(-20024,'Score de sensores disponivel apenas para cao e gato');
    END IF;
    IF v_especie = 'GATO' THEN
        v_temp_min := 38.0;  v_temp_max := 39.5;
        v_fc_min   := 120;   v_fc_max   := 220;
        v_ativ_min := 30;
    ELSE
        v_temp_min := 37.5;  v_temp_max := 39.2;
        v_fc_min   := 60;    v_fc_max   := 140;
        v_ativ_min := 40;
    END IF;

    -- 3) somatorio manual das leituras (sem SUM / AVG)
    FOR r IN (SELECT temperatura, freq_cardiaca, spo2, atividade
                FROM CV4_LEITURA_SENSOR
               WHERE id_pet = p_pet_id) LOOP
        v_qtd       := v_qtd + 1;
        v_soma_temp := v_soma_temp + r.temperatura;
        v_soma_fc   := v_soma_fc   + r.freq_cardiaca;
        v_soma_spo2 := v_soma_spo2 + r.spo2;
        v_soma_ativ := v_soma_ativ + r.atividade;
    END LOOP;

    -- 4) medias (ZERO_DIVIDE se o pet nao possui leituras)
    v_med_temp := v_soma_temp / v_qtd;
    v_med_fc   := v_soma_fc   / v_qtd;
    v_med_spo2 := v_soma_spo2 / v_qtd;
    v_med_ativ := v_soma_ativ / v_qtd;

    -- 5) sub-scores: fator calibrado para que o desvio "grave" de cada sinal valha 100
    v_sub_temp := sub_score(v_med_temp, v_temp_min, v_temp_max, 125);  -- 0,8 C fora da faixa
    v_sub_fc   := sub_score(v_med_fc,   v_fc_min,   v_fc_max,   2.5);  -- 40 bpm fora da faixa
    v_sub_spo2 := sub_score(v_med_spo2, v_spo2_min, NULL,       20);   -- 5 pontos abaixo de 95%
    v_sub_ativ := sub_score(v_med_ativ, v_ativ_min, NULL,       4);    -- 25 pontos abaixo do minimo

    -- 6) score ponderado
    v_score := ROUND(0.40 * v_sub_temp + 0.25 * v_sub_fc + 0.20 * v_sub_spo2 + 0.15 * v_sub_ativ, 1);

    -- linha de diagnostico para conferencia do calculo
    DBMS_OUTPUT.PUT_LINE('[FN_CALC_RISCO_PET] ' || RPAD(v_nome, 6) || ' (' || RPAD(v_especie, 4) || ') '
                         || v_qtd || ' leituras | medias: temp ' || fmt(v_med_temp) || 'C, fc ' || fmt(v_med_fc)
                         || ' bpm, spo2 ' || fmt(v_med_spo2) || '%, ativ ' || fmt(v_med_ativ)
                         || ' | score ' || fmt(v_score) || ' -> ' || classificar(v_score));
    RETURN v_score;

EXCEPTION
 WHEN e_param_invalido THEN RAISE_APPLICATION_ERROR(-20021,'Risco: id do pet deve ser positivo');
 WHEN NO_DATA_FOUND THEN RAISE_APPLICATION_ERROR(-20022,'Risco: pet inexistente');
 WHEN ZERO_DIVIDE THEN RAISE_APPLICATION_ERROR(-20023,'Risco: pet sem leituras de sensor');
 WHEN OTHERS THEN RAISE;
END FN_CALC_RISCO_PET;
 PROCEDURE PRC_CATALOGOS(p_veterinario VARCHAR2,p_tipo VARCHAR2,p_vet_id IN OUT NUMBER,p_servico_id IN OUT NUMBER) IS
  v_nome VARCHAR2(100); v_codigo VARCHAR2(30);
 BEGIN
  IF TRIM(p_veterinario) IS NULL OR p_tipo IS NULL THEN RAISE_APPLICATION_ERROR(-20025,'Veterinario e tipo obrigatorios'); END IF;
  SELECT id_veterinario INTO p_vet_id FROM CV4_VETERINARIO WHERE UPPER(TRIM(nome))=UPPER(TRIM(p_veterinario));
  IF p_servico_id IS NULL THEN
   SELECT id_tipo_servico INTO p_servico_id FROM
    (SELECT id_tipo_servico FROM CV4_TIPO_SERVICO WHERE codigo_app=p_tipo ORDER BY id_tipo_servico) WHERE ROWNUM=1;
  END IF;
  SELECT codigo_app INTO v_codigo FROM CV4_TIPO_SERVICO WHERE id_tipo_servico=p_servico_id;
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
  p_id:=CV4_SEQ_LEITURA.NEXTVAL;
  INSERT INTO CV4_LEITURA_SENSOR VALUES(p_id,p_pet,TRIM(p_dispositivo),SYSTIMESTAMP,p_temperatura,p_fc,p_spo2,p_atividade);
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
   SELECT id_clinica INTO v_existe FROM CV4_CLINICA WHERE id_clinica=p_clinica_id;
  END IF;
  DBMS_LOB.CREATETEMPORARY(p_resultado,TRUE);
  DBMS_LOB.WRITEAPPEND(p_resultado,1,'[');
  -- Mesmo JOIN das seis entidades aprovadas na Sprint 3.
  FOR r IN (SELECT a.*,c.nome clinica_nome,c.cidade,v.nome vet_nome,v.crmv,v.especialidade,
   ts.descricao servico_nome,p.nome pet_nome,p.especie,p.raca,p.sexo,p.peso_kg,
   t.id_tutor,t.nome tutor_nome
   FROM CV4_ATENDIMENTO a JOIN CV4_CLINICA c ON c.id_clinica=a.id_clinica
   JOIN CV4_VETERINARIO v ON v.id_veterinario=a.id_veterinario
   JOIN CV4_TIPO_SERVICO ts ON ts.id_tipo_servico=a.id_tipo_servico
   JOIN CV4_PET p ON p.id_pet=a.id_pet JOIN CV4_TUTOR t ON t.id_tutor=p.id_tutor
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
  FOR r IN (SELECT id_clinica,id_tipo_servico,valor FROM CV4_ATENDIMENTO WHERE status='REALIZADO'
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
  INSERT INTO CV4_AUD_PET(id_registro,tipo_operacao,nome_usuario,data_hora,valor_anterior,valor_novo,
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
CREATE OR REPLACE TRIGGER TRG_CV4_AUD_PET AFTER INSERT OR UPDATE OR DELETE ON tb_pet FOR EACH ROW
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
CREATE OR REPLACE TRIGGER TRG_CV4_CONSULTA_CAT
BEFORE INSERT OR UPDATE OF veterinario,tipo_consulta,id_veterinario,id_tipo_servico ON tb_consulta FOR EACH ROW
DECLARE v_vet NUMBER; v_serv NUMBER;
BEGIN
 v_vet:=:NEW.id_veterinario; v_serv:=:NEW.id_tipo_servico;
 IF UPDATING AND :NEW.tipo_consulta<>:OLD.tipo_consulta THEN v_serv:=NULL; END IF;
 PKG_CLYVO_CLINICO.PRC_CATALOGOS(:NEW.veterinario,:NEW.tipo_consulta,v_vet,v_serv);
 :NEW.id_veterinario:=v_vet; :NEW.id_tipo_servico:=v_serv;
END;
/
