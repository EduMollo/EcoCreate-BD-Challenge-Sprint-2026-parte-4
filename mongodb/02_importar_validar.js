// Importacao real do JSON exportado pelo package; nenhuma carga JSON inventada.
// Upsert por chave de origem permite repetir o processo sem duplicar documentos.
const fs = require('fs');
const arquivo = process.env.DATASET_PATH || '/dataset/2TDSPF_2026_Atendimentos.json';
const documentos = JSON.parse(fs.readFileSync(arquivo, 'utf8').replace(/^\uFEFF/, ''));
assert(Array.isArray(documentos), 'O dataset deve ser um array JSON');
assert(documentos.length > 0, 'Dataset vazio: registrar atendimentos antes da demonstracao');
const banco = db.getSiblingDB('clyvovet_sprint4');
assert(banco.getCollectionNames().includes('atendimentos'), 'Execute primeiro 01_criar_estrutura.js');
const ids = new Set();
for (const item of documentos) {
  assert(Number.isSafeInteger(item.id_atendimento) && item.id_atendimento>0, 'ID invalido');
  assert(!ids.has(item.id_atendimento), 'ID duplicado no dataset');
  ids.add(item.id_atendimento);
  // O JSON permanece exatamente como exportado. Campos BSON derivados sao explicitos.
  const convertido = {...item, data_bson: new Date(item.data+'T00:00:00.000Z'),
    valor_decimal: item.valor === null ? null : NumberDecimal(String(item.valor))};
  assert(!isNaN(convertido.data_bson.getTime()), 'Data invalida');
  banco.atendimentos.replaceOne({id_atendimento:item.id_atendimento}, convertido, {upsert:true});
}
const presentes = banco.atendimentos.countDocuments({id_atendimento:{$in:[...ids]}});
assert(documentos.length === presentes, 'Contagem importada divergente');
// Compara todos os campos originais de cada documento; derivados nao alteram o dataset.
function iguais(a,b) {
  if(a===null || typeof a!=='object') return a===b;
  return Object.keys(a).every(k => iguais(a[k],b[k]));
}
for(const original of documentos) {
  const salvo=banco.atendimentos.findOne({id_atendimento:original.id_atendimento});
  assert(iguais(original,salvo), 'Conteudo divergente no atendimento '+original.id_atendimento);
}
printjson({arquivo, documentos_no_json:documentos.length, documentos_conferidos:presentes,
  total_na_colecao:banco.atendimentos.countDocuments(), resultado:'IMPORTACAO E CONTEUDO CONFERIDOS'});
