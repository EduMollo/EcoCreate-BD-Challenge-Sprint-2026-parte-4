const banco = db.getSiblingDB('clyvovet_sprint4');
print('Documento com entidades aninhadas:');
printjson(banco.atendimentos.findOne({}, {_id:0}));
print('Historico do pet 1:');
printjson(banco.atendimentos.find({'pet.id':1},{_id:0}).sort({data:-1}).toArray());
print('Faturamento 2026 por clinica (comparar com Oracle):');
printjson(banco.atendimentos.aggregate([
  {$match:{status:'REALIZADO', data:{$gte:'2026-01-01',$lt:'2027-01-01'}}},
  {$group:{_id:'$clinica.id', clinica:{$first:'$clinica.nome'}, total:{$sum:'$valor_decimal'}, quantidade:{$sum:1}}},
  {$sort:{_id:1}}
]).toArray());
print('Indices:'); printjson(banco.atendimentos.getIndexes());
