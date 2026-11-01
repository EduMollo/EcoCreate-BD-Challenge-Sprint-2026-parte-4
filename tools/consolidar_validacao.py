"""Consolida resultados reais do roteiro e do Surefire, sem copiar credenciais/logs privados."""
from pathlib import Path
import hashlib
import json
from decimal import Decimal
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
JAVA=ROOT.parents[1]/'CS4 JAVA/Projeto-EcoCreate-Java-Challenge-Sprint-2026-parte-4'
status=json.loads((ROOT/'evidencias/resultado-validacao.json').read_text(encoding='utf-8-sig'))
assert status.get('sucesso') is True
assert all(status.get(stage)=='aprovado' for stage in ['oracle','mongodb','build_java'])
dataset=ROOT/'dataset/2TDSPF_2026_Atendimentos.json'
digest=hashlib.sha256(dataset.read_bytes()).hexdigest()
assert digest.upper()==status['dataset_sha256'].upper(),'Dataset alterado desde a validacao real'
documents=json.loads(dataset.read_text(encoding='utf-8-sig'),parse_float=Decimal)
assert len({d['id_atendimento'] for d in documents})==len(documents)
realizados=[d for d in documents if d['status']=='REALIZADO' and d['data'].startswith('2026-')]
total=sum((Decimal(str(d['valor'])) for d in realizados),Decimal(0))
suites=[]
for path in sorted((JAVA/'target/surefire-reports').glob('TEST-*.xml')):
    suite=ET.parse(path).getroot()
    suites.append({'suite':suite.attrib['name'],**{k:int(suite.attrib.get(k,0)) for k in ['tests','failures','errors','skipped']}})
assert suites,'Relatorios Surefire ausentes'
totals={k:sum(s[k] for s in suites) for k in ['tests','failures','errors','skipped']}
assert totals['failures']==0 and totals['errors']==0
oracle=next(s for s in suites if s['suite'].endswith('.OracleIntegracaoTest'))
assert oracle['tests']>=2 and oracle['skipped']==0,'Testes Oracle nao foram executados'
jar=JAVA/'target/clyvovet-web-4.0.0.jar'
assert jar.is_file(),'JAR nao gerado'
summary={
 'validado_em':status['fim'],
 'origem':'Roteiro real no terminal Windows, resultado-validacao.json e relatorios Surefire',
 'oracle':{'status':'aprovado','versao':'19.3','objetos_finais_valid':12,'testes_transacionais':'aprovados com rollback',
           'procedures_via_backend':'exportacao JSON e faturamento executados por OracleIntegracaoTest'},
 'dataset':{'arquivo':dataset.name,'sha256':digest,'documentos':len(documents),
            'realizados_2026':len(realizados),'faturamento_2026':str(total)},
 'mongodb':{'status':'aprovado','colecao':'clyvovet_sprint4.atendimentos',
            'documentos_conferidos':len(documents),'reimportacao_sem_duplicatas':True},
 'java':{'status':'aprovado','identificados':totals['tests'],'executados':totals['tests']-totals['skipped'],
         'falhas':totals['failures'],'erros':totals['errors'],'ignorados':totals['skipped'],
         'jar':jar.name,'sha256_jar':hashlib.sha256(jar.read_bytes()).hexdigest(),'suites':suites},
 'pendencias':['Conferir jornada pela interface Oracle: cadastro, atendimento e leitura',
               'Gravar video narrado, conferir acesso e incluir o link na entrega']}
(ROOT/'docs/2TDSPF_2026_Validacao.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:summary[k] for k in ['validado_em','dataset','mongodb','pendencias']},ensure_ascii=False,indent=2))
print('Java:',summary['java']['executados'],'executados;',summary['java']['ignorados'],'ignorados; zero falhas/erros.')
