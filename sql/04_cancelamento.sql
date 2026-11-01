-- Evolucao do schema: o cancelamento de consulta passou a exigir um motivo.
alter table tb_consulta add motivo_cancelamento varchar2(300);
