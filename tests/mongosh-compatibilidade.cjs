// Verifica compatibilidade do codigo de shell, sem substituir o MongoDB real.
const test = require('node:test');
const check = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const criar = fs.readFileSync(path.join(root,'mongodb/01_criar_estrutura.js'),'utf8');
const importar = fs.readFileSync(path.join(root,'mongodb/02_importar_validar.js'),'utf8');
const dataset = path.join(root,'dataset/2TDSPF_2026_Atendimentos.json');
function contexto(banco) {
  return {db:{getSiblingDB:()=>banco},
    // Deliberadamente sem assert.eq ou assert.commandWorked.
    assert:(condition,message)=>check.ok(condition,message),
    print:()=>{},printjson:()=>{},require,
    process:{env:{DATASET_PATH:dataset}},NumberDecimal:value=>({decimal:value})};
}
test('cria colecao nova com assert simples',()=>{
  let criada=false;let indices=0;
  const banco={getCollectionNames:()=>[],createCollection:()=>{criada=true;},
    atendimentos:{createIndex:()=>{indices++;}}};
  vm.runInNewContext(criar,contexto(banco));
  check.ok(criada);check.equal(indices,3);
});
test('atualiza validador de colecao existente sem helpers legados',()=>{
  let atualizado=false;
  const banco={getCollectionNames:()=>['atendimentos'],runCommand:()=>{atualizado=true;return {ok:1};},
    atendimentos:{createIndex:()=>{}}};
  vm.runInNewContext(criar,contexto(banco));check.ok(atualizado);
});
test('interrompe quando collMod e rejeitado',()=>{
  const banco={getCollectionNames:()=>['atendimentos'],runCommand:()=>({ok:0,errmsg:'rejeitado'}),
    atendimentos:{createIndex:()=>check.fail('Nao deve criar indices apos erro')}};
  check.throws(()=>vm.runInNewContext(criar,contexto(banco)),/Falha ao atualizar o validador/);
});
test('importa e reimporta o JSON real sem duplicar IDs no contrato do shell', {skip:!fs.existsSync(dataset)},()=>{
  const registros=new Map();
  const banco={getCollectionNames:()=>['atendimentos'],atendimentos:{
    replaceOne:(filter,documento,opcoes)=>{check.ok(opcoes.upsert);registros.set(filter.id_atendimento,documento);},
    countDocuments:()=>registros.size,
    findOne:filter=>registros.get(filter.id_atendimento)
  }};
  vm.runInNewContext(importar,contexto(banco));
  const esperado=JSON.parse(fs.readFileSync(dataset,'utf8').replace(/^\uFEFF/,''));
  check.equal(registros.size,esperado.length);
  vm.runInNewContext(importar,contexto(banco));
  check.equal(registros.size,esperado.length);
});
