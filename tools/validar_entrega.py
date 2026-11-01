"""Verificacoes locais de consistencia. Nao compila PL/SQL e nao substitui bancos reais."""
from pathlib import Path
from decimal import Decimal
import hashlib
import json
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
JAVA=ROOT.parents[1]/'CS4 JAVA/Projeto-EcoCreate-Java-Challenge-Sprint-2026-parte-4'
sql=(ROOT/'sql/2TDSPF_2026_CodigoSql_Integrantes.sql').read_text(encoding='utf-8')
packages=(ROOT/'sql/07_packages_gatilhos.sql').read_text(encoding='utf-8')
seed=(ROOT/'sql/09_dados_demonstracao.sql').read_text(encoding='utf-8')
assert not re.search(r'\bDROP\s+(TABLE|PACKAGE|VIEW|TRIGGER|USER)',sql,re.I),'Instalador destrutivo'
assert len(re.findall(r'CREATE\s+TABLE\b',sql,re.I))==14,'Numero inesperado de tabelas'
assert len(re.findall(r'CREATE OR REPLACE PACKAGE (?!BODY)',packages,re.I))==5,'Packages incompletos'
assert len(re.findall(r'CREATE OR REPLACE PACKAGE BODY',packages,re.I))==5,'Bodies incompletos'
assert len(re.findall(r'CREATE OR REPLACE TRIGGER',packages,re.I))==2,'Gatilhos incompletos'
assert not re.search(r'\b(?:JSON_OBJECT|JSON_ARRAYAGG|JSON_ARRAY|TO_JSON|APEX_JSON)\s*\(',packages,re.I),'Conversao deixou de ser manual'
for name in re.findall(r'\bCONSTRAINT\s+(\w+)',sql,re.I):
    assert name.upper().startswith('CV4_'),f'Constraint sem namespace: {name}'
    assert len(name)<=30,f'Nome Oracle longo: {name}'
for name in re.findall(r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(\w+)',sql,re.I):
    assert name.upper().startswith('CV4_') and len(name)<=30,name
counts={t:len(re.findall(r'INSERT INTO\s+'+t+r'\b',seed,re.I)) for t in ['tb_clinica','tb_tutor','tb_pet','tb_consulta','CV4_LEITURA_SENSOR']}
assert list(counts.values())==[6,8,10,34,20],counts
total=Decimal(0);realizados=0
for line in seed.splitlines():
    if line.upper().startswith('INSERT INTO TB_CONSULTA') and "'CONCLUIDA'" in line:
        match=re.search(r"TO_DATE\('([^']+)',\s*'[^']+'\),\s*([\d.]+),",line)
        assert match,line
        if match[1].endswith('2026'):total+=Decimal(match[2]);realizados+=1
assert total==Decimal('15635.00') and realizados==30,(total,realizados)
for source in ['01_estrutura.sql','02_constraints.sql','03_perfis.sql','04_cancelamento.sql']:
    version=source[:2].lstrip('0');stem=source[3:]
    assert (ROOT/'sql'/source).read_bytes()==(JAVA/f'src/main/resources/db/oracle-sprint4/V{version}__{stem}').read_bytes()
models=json.loads((ROOT/'docs/dicionario_modelo.json').read_text(encoding='utf-8'))
assert len(models)==14
pdfs={}
for filename in ['2TDSPF_2026_Proj_BD.pdf','2TDSPF_2026_Modelo_Logico.pdf','2TDSPF_2026_Modelo_Fisico.pdf']:
    data=(ROOT/'docs'/filename).read_bytes()
    assert data.startswith(b'%PDF-1.4') and data.rstrip().endswith(b'%%EOF')
    pages=int(re.search(rb'/Type /Pages /Count (\d+)',data)[1]);assert pages>0
    pdfs[filename]={'paginas':pages,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
dataset=ROOT/'dataset/2TDSPF_2026_Atendimentos.json'
dataset_status='PENDENTE: exportacao real do Oracle FIAP'
if dataset.exists():
    documents=json.loads(dataset.read_text(encoding='utf-8-sig'))
    assert isinstance(documents,list) and documents
    ids=[d['id_atendimento'] for d in documents];assert len(ids)==len(set(ids))
    for item in documents:
        for key in ['clinica','pet','tutor','veterinario','servico']:assert isinstance(item[key],dict)
    dataset_status=f'JSON estruturalmente valido: {len(documents)} documentos; conferir origem no log Oracle'
report={'tipo':'Verificacao local estatica; nao e evidencia de execucao Oracle/MongoDB',
 'tabelas':14,'packages':5,'gatilhos':2,'carga':counts,'total_esperado_2026':str(total),
 'atendimentos_realizados_2026':realizados,'pdfs':pdfs,'dataset':dataset_status}
(ROOT/'docs/VALIDACAO-LOCAL.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
