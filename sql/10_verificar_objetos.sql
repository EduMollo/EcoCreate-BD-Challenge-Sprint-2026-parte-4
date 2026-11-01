SET SERVEROUTPUT ON
-- A sincronizacao IDENTITY da carga pode invalidar dependentes. Recompilar
-- os objetos deste projeto antes de exibir e verificar o status final.
ALTER PACKAGE PKG_CLYVO_JSON COMPILE BODY;
ALTER PACKAGE PKG_CLYVO_CLINICO COMPILE BODY;
ALTER PACKAGE PKG_CLYVO_RELATORIOS COMPILE BODY;
ALTER PACKAGE PKG_CLYVO_AUDITORIA COMPILE BODY;
ALTER PACKAGE PKG_CLYVOVET COMPILE BODY;
ALTER TRIGGER TRG_CV4_AUD_PET COMPILE;
ALTER TRIGGER TRG_CV4_CONSULTA_CAT COMPILE;
SELECT object_type,object_name,status FROM user_objects
 WHERE object_name LIKE 'PKG_CLYVO%' OR object_name IN ('TRG_CV4_AUD_PET','TRG_CV4_CONSULTA_CAT') ORDER BY object_name,object_type;
SELECT name,type,line,position,text FROM user_errors WHERE name LIKE 'PKG_CLYVO%' OR name IN ('TRG_CV4_AUD_PET','TRG_CV4_CONSULTA_CAT');
DECLARE v_erros NUMBER; v_pendentes NUMBER; v_invalidos NUMBER; v_objetos NUMBER;
BEGIN
 SELECT COUNT(*) INTO v_erros FROM user_errors WHERE name LIKE 'PKG_CLYVO%' OR name IN ('TRG_CV4_AUD_PET','TRG_CV4_CONSULTA_CAT');
 IF v_erros>0 THEN RAISE_APPLICATION_ERROR(-20902,'Objetos com erros de compilacao'); END IF;
 SELECT COUNT(*),COUNT(CASE WHEN status<>'VALID' THEN 1 END) INTO v_objetos,v_invalidos
 FROM user_objects WHERE object_name IN ('PKG_CLYVO_JSON','PKG_CLYVO_CLINICO','PKG_CLYVO_RELATORIOS',
 'PKG_CLYVO_AUDITORIA','PKG_CLYVOVET','TRG_CV4_AUD_PET','TRG_CV4_CONSULTA_CAT');
 IF v_objetos<>12 OR v_invalidos>0 THEN RAISE_APPLICATION_ERROR(-20902,'Objetos ausentes ou INVALID apos recompilacao'); END IF;
 SELECT COUNT(*) INTO v_pendentes FROM tb_consulta WHERE id_veterinario IS NULL OR id_tipo_servico IS NULL;
 IF v_pendentes>0 THEN RAISE_APPLICATION_ERROR(-20903,'Consultas antigas sem catalogos: fazer conciliacao antes da exportacao'); END IF;
 DBMS_OUTPUT.PUT_LINE('Compilacao e catalogos consistentes.');
END;
/
SELECT 'TB_PET' tabela,COUNT(*) quantidade FROM tb_pet UNION ALL SELECT 'CV4_PET (view)',COUNT(*) FROM CV4_PET
UNION ALL SELECT 'TB_CONSULTA',COUNT(*) FROM tb_consulta UNION ALL SELECT 'CV4_ATENDIMENTO (view)',COUNT(*) FROM CV4_ATENDIMENTO;
SELECT id_auditoria,id_registro,tipo_operacao,nome_usuario,data_hora FROM CV4_AUD_PET ORDER BY id_auditoria;
