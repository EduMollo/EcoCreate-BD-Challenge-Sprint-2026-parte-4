// Executar ANTES de importar. Colecao de leitura analitica; Oracle e a origem.
const banco = db.getSiblingDB('clyvovet_sprint4');
const validator = {$jsonSchema: {
  bsonType: 'object',
  required: ['id_atendimento', 'data', 'status', 'valor', 'clinica', 'pet', 'tutor', 'veterinario', 'servico'],
  properties: {
    id_atendimento: {bsonType: ['int','long','double','decimal'], minimum: 1},
    data: {bsonType: 'string', pattern: '^\\d{4}-\\d{2}-\\d{2}$'},
    status: {enum: ['REALIZADO','AGENDADO','CANCELADO','EM_ANDAMENTO']},
    valor: {bsonType: ['int','long','double','decimal','null'], minimum: 0},
    clinica: {bsonType: 'object', required: ['id','nome','cidade']},
    pet: {bsonType: 'object', required: ['id','nome','especie','peso_kg']},
    tutor: {bsonType: 'object', required: ['id','nome']},
    veterinario: {bsonType: 'object', required: ['id','nome','crmv']},
    servico: {bsonType: 'object', required: ['id','descricao']}
  }
}};
if (!banco.getCollectionNames().includes('atendimentos')) {
  banco.createCollection('atendimentos', {validator, validationLevel: 'strict', validationAction: 'error'});
} else {
  const resultado = banco.runCommand({collMod:'atendimentos', validator, validationLevel:'strict', validationAction:'error'});
  assert(resultado.ok === 1, 'Falha ao atualizar o validador: '+(resultado.errmsg || 'comando rejeitado'));
}
banco.atendimentos.createIndex({id_atendimento:1}, {unique:true, name:'uk_atendimento_oracle'});
banco.atendimentos.createIndex({'pet.id':1, data:-1}, {name:'ix_pet_data'});
banco.atendimentos.createIndex({'clinica.id':1, status:1, data:-1}, {name:'ix_clinica_status_data'});
print('Estrutura pronta: clyvovet_sprint4.atendimentos');
