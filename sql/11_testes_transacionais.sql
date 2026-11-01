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
 SELECT COUNT(*) INTO v_aud FROM CV4_AUD_PET WHERE id_registro=1;
 UPDATE tb_pet SET peso_kg=v_peso+0.1 WHERE id=1;
 DECLARE v_depois NUMBER; BEGIN
  SELECT COUNT(*) INTO v_depois FROM CV4_AUD_PET WHERE id_registro=1;
  exigir(v_depois=v_aud+1,'Trigger nao auditou UPDATE');
 END;
 INSERT INTO tb_pet(nome,especie,raca,data_nascimento,peso_kg,sexo,ativo,id_tutor)
 VALUES('Pet teste transacional','CACHORRO','SRD',DATE '2024-01-01',10,'MACHO',1,1) RETURNING id INTO v_id;
 DELETE FROM tb_pet WHERE id=v_id;
 DECLARE v_total NUMBER; BEGIN
  SELECT COUNT(*) INTO v_total FROM CV4_AUD_PET WHERE id_registro=v_id;
  exigir(v_total=2,'Auditoria INSERT e DELETE ausente');
 END;
 ROLLBACK TO teste_sprint4;
 DBMS_OUTPUT.PUT_LINE('Testes concluidos; DML de teste revertido.');
EXCEPTION WHEN OTHERS THEN ROLLBACK TO teste_sprint4; RAISE;
END;
/
