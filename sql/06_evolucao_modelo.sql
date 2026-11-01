-- Sprint 4: complementos do modelo Java; nao remove tabelas/dados anteriores.
-- Executar somente depois das migrations Oracle V1 a V5, em schema de teste.
CREATE TABLE CV4_VETERINARIO (
 id_veterinario NUMBER(6) CONSTRAINT CV4_pk_cv4_veterinario PRIMARY KEY,
 nome VARCHAR2(100) NOT NULL, crmv VARCHAR2(20) NOT NULL,
 especialidade VARCHAR2(60),
 CONSTRAINT CV4_uk_cv4_vet_crmv UNIQUE(crmv));
CREATE UNIQUE INDEX CV4_uk_veterinario_nome ON CV4_VETERINARIO(UPPER(TRIM(nome)));
CREATE SEQUENCE CV4_SEQ_VETERINARIO START WITH 1000 NOCACHE;
CREATE TABLE CV4_TIPO_SERVICO (
 id_tipo_servico NUMBER(6) CONSTRAINT CV4_pk_cv4_tipo_servico PRIMARY KEY,
 descricao VARCHAR2(60) NOT NULL, preco_base NUMBER(10,2) NOT NULL,
 codigo_app VARCHAR2(30) NOT NULL,
 CONSTRAINT CV4_ck_cv4_servico_preco CHECK(preco_base > 0));
CREATE TABLE CV4_LEITURA_SENSOR (
 id_leitura NUMBER(10) CONSTRAINT CV4_pk_cv4_leitura PRIMARY KEY,
 id_pet NUMBER(19) NOT NULL CONSTRAINT CV4_fk_cv4_leitura_pet REFERENCES tb_pet(id),
 dispositivo VARCHAR2(30) NOT NULL, data_hora TIMESTAMP NOT NULL,
 temperatura NUMBER(4,1) NOT NULL, freq_cardiaca NUMBER(4) NOT NULL,
 spo2 NUMBER(5,1) NOT NULL, atividade NUMBER(5,1) NOT NULL,
 CONSTRAINT CV4_ck_leitura_temp CHECK(temperatura BETWEEN 20 AND 50),
 CONSTRAINT CV4_ck_leitura_fc CHECK(freq_cardiaca BETWEEN 1 AND 400),
 CONSTRAINT CV4_ck_leitura_spo2 CHECK(spo2 BETWEEN 0 AND 100),
 CONSTRAINT CV4_ck_leitura_atividade CHECK(atividade BETWEEN 0 AND 100));
CREATE SEQUENCE CV4_SEQ_LEITURA START WITH 1000 NOCACHE;
CREATE INDEX CV4_ix_leitura_pet_data ON CV4_LEITURA_SENSOR(id_pet, data_hora);
ALTER TABLE tb_consulta ADD (id_veterinario NUMBER(6), id_tipo_servico NUMBER(6));
ALTER TABLE tb_consulta ADD CONSTRAINT CV4_fk_consulta_veterinario FOREIGN KEY(id_veterinario) REFERENCES CV4_VETERINARIO;
ALTER TABLE tb_consulta ADD CONSTRAINT CV4_fk_consulta_servico FOREIGN KEY(id_tipo_servico) REFERENCES CV4_TIPO_SERVICO;
ALTER TABLE tb_consulta MODIFY (id_veterinario NOT NULL,id_tipo_servico NOT NULL);
CREATE INDEX CV4_ix_consulta_veterinario ON tb_consulta(id_veterinario);
CREATE INDEX CV4_ix_consulta_servico ON tb_consulta(id_tipo_servico);
ALTER TABLE CV4_AUD_PET ADD (nome_tabela VARCHAR2(30) DEFAULT 'TB_PET' NOT NULL,
 usuario_so VARCHAR2(100), maquina VARCHAR2(100), usuario_aplicacao VARCHAR2(100));
ALTER TABLE CV4_AUD_PET ADD CONSTRAINT CV4_ck_aud_operacao CHECK(tipo_operacao IN ('INSERT','UPDATE','DELETE'));
CREATE INDEX CV4_ix_aud_pet_data ON CV4_AUD_PET(id_registro, data_hora);
CREATE OR REPLACE VIEW CV4_CLINICA AS SELECT id id_clinica,nome,cidade,endereco,telefone FROM tb_clinica;
CREATE OR REPLACE VIEW CV4_TUTOR AS SELECT id id_tutor,nome,cpf,email,telefone FROM tb_tutor;
CREATE OR REPLACE VIEW CV4_PET AS SELECT id id_pet,id_tutor,nome,
 CASE especie WHEN 'CACHORRO' THEN 'CAO' ELSE especie END especie,raca,
 CASE sexo WHEN 'MACHO' THEN 'M' WHEN 'FEMEA' THEN 'F' END sexo,
 data_nascimento,peso_kg FROM tb_pet;
CREATE OR REPLACE VIEW CV4_ATENDIMENTO AS SELECT id id_atendimento,id_pet,id_clinica,
 id_veterinario,id_tipo_servico,veterinario,tipo_consulta,
 data_consulta data_atendimento,valor,
 CASE status WHEN 'CONCLUIDA' THEN 'REALIZADO' WHEN 'CANCELADA' THEN 'CANCELADO'
 WHEN 'AGENDADA' THEN 'AGENDADO' ELSE 'EM_ANDAMENTO' END status FROM tb_consulta;
