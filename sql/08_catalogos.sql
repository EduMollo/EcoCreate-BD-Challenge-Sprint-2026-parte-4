-- Carga de catalogos ficticios aprovada/adaptada. Executar uma vez.
INSERT INTO CV4_VETERINARIO (id_veterinario, nome, crmv, especialidade) VALUES (1, 'Dra. Mariana Costa',    'CRMV-SP 12345', 'Clinica geral');
INSERT INTO CV4_VETERINARIO (id_veterinario, nome, crmv, especialidade) VALUES (2, 'Dr. Rafael Almeida',    'CRMV-SP 23456', 'Cirurgia');
INSERT INTO CV4_VETERINARIO (id_veterinario, nome, crmv, especialidade) VALUES (3, 'Dra. Juliana Ferreira', 'CRMV-SP 34567', 'Dermatologia');
INSERT INTO CV4_VETERINARIO (id_veterinario, nome, crmv, especialidade) VALUES (4, 'Dr. Thiago Barbosa',    'CRMV-SP 45678', 'Cardiologia');
INSERT INTO CV4_VETERINARIO (id_veterinario, nome, crmv, especialidade) VALUES (5, 'Dra. Patricia Gomes',   'CRMV-SP 56789', 'Diagnostico por imagem');
INSERT INTO CV4_VETERINARIO (id_veterinario, nome, crmv, especialidade) VALUES (6, 'Dr. Lucas Moreira',     'CRMV-SP 67890', 'Clinica geral');
INSERT INTO CV4_TIPO_SERVICO VALUES(1,'Consulta clinica',180,'ROTINA');
INSERT INTO CV4_TIPO_SERVICO VALUES(2,'Vacinacao',120,'VACINACAO');
INSERT INTO CV4_TIPO_SERVICO VALUES(3,'Exames laboratoriais',250,'EXAME');
INSERT INTO CV4_TIPO_SERVICO VALUES(4,'Cirurgia',1500,'CIRURGIA');
INSERT INTO CV4_TIPO_SERVICO VALUES(5,'Ultrassonografia',320,'EXAME');
INSERT INTO CV4_TIPO_SERVICO VALUES(6,'Retorno',90,'RETORNO');
INSERT INTO CV4_TIPO_SERVICO VALUES(7,'Consulta preventiva',180,'PREVENTIVA');
INSERT INTO CV4_TIPO_SERVICO VALUES(8,'Emergencia',350,'EMERGENCIA');
COMMIT;
