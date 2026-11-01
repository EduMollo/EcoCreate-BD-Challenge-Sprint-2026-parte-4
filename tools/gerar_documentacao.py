"""Documentacao e diagramas vetoriais; nao fabrica evidencias de execucao."""
from pathlib import Path
from html import escape as esc
import re
import json
from datetime import date

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs'
DOC.mkdir(exist_ok=True)
TEAM=[('Carlos Alberto Guedes Neto','566022'),('Eduardo Novaes Mollo','561515'),
 ('Luan Peixoto Marins Rocha','562258'),('Mathaus Victor Souza Marcelino','564146'),
 ('Vinicius Luis Exposito Morassi','563340')]
STYLE="""
@page {size:A4; margin:15mm 14mm;}
*{box-sizing:border-box} body{font:11px/1.5 Arial,sans-serif;color:#203344;margin:0}
.page{break-after:page;position:relative} .page:last-child{break-after:auto}
.eyebrow{color:#147d87;text-transform:uppercase;letter-spacing:2px;font-size:10px;font-weight:bold}
h1{font-size:34px;line-height:1.12;color:#132e45;margin:16px 0} h2{font-size:23px;color:#132e45;margin:12px 0}
h3{font-size:14px;color:#147d87;margin:14px 0 5px} p{margin:6px 0 10px}
table{border-collapse:collapse;width:100%;margin:8px 0 16px;font-size:10px}
th{text-align:left;background:#173b50;color:white;padding:7px} td{padding:6px 7px;border-bottom:1px solid #dbe5e9;vertical-align:top}
tr:nth-child(even) td{background:#f2f7f8} tr{break-inside:avoid}
code{font-family:Consolas,monospace;font-size:10px;overflow-wrap:anywhere}
pre{background:#eef4f6;border-left:3px solid #147d87;padding:12px;font:10px/1.5 Consolas,monospace;white-space:pre-wrap}
.callout{border-left:4px solid #147d87;background:#eaf5f4;padding:12px;margin:15px 0}
.muted{color:#607785}.cover{padding-top:40px;min-height:930px}.rule{height:6px;background:#147d87;width:70px;margin:25px 0}
.pill{display:inline-block;background:#e3f3f0;color:#176b60;padding:5px 9px;font-size:10px;font-weight:bold}
.footer{border-top:1px solid #dbe5e9;padding-top:8px;margin-top:20px;font-size:9px;color:#667c8d}
svg{width:100%;height:auto} .schema{font-size:9px}.schema td{padding:4px 6px}.schema th{padding:5px 6px}
.schema code{font-size:9px}.small{font-size:10px}
"""

def table(headers, rows, cls=''):
    return f'<table class="{cls}"><thead><tr>'+''.join(f'<th>{esc(str(h))}</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{esc(str(c))}</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table>'

def page(title,content,kind='DOCUMENTAÇÃO TÉCNICA'):
    return f'<section class="page"><div class="eyebrow">ClyvoVet / Sprint 4 / {kind}</div><h2>{title}</h2>{content}<div class="footer">FIAP • 2TDSPF • Mastering Relational and Non-Relational Database • Entrega 04/11/2026</div></section>'

def document(title,pages,name):
    output='<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>'+esc(title)+'</title><style>'+STYLE+'</style><body>'+''.join(pages)+'</body></html>'
    (DOC/name).write_text(output,encoding='utf-8')

def diagram(physical=False):
    names=['TUTOR','PET','LEITURA_SENSOR','VETERINARIO','ATENDIMENTO','TIPO_SERVICO','CLINICA','AUD_PET']
    mapping=['TB_TUTOR','TB_PET','CV4_LEITURA_SENSOR','CV4_VETERINARIO','TB_CONSULTA','CV4_TIPO_SERVICO','TB_CLINICA','CV4_AUD_PET']
    pos=[(20,15),(20,225),(20,435),(350,15),(350,225),(350,435),(680,15),(680,435)]
    fields=[['PK id_tutor','nome, cpf, email'],['PK id_pet','FK id_tutor','nome, especie, peso_kg'],
      ['PK id_leitura','FK id_pet','data_hora, sinais vitais'],['PK id_veterinario','nome, crmv'],
      ['PK id_atendimento','FK pet, clinica','FK veterinario, servico','data, valor, status'],
      ['PK id_tipo_servico','descricao, preco_base'],['PK id_clinica','nome, cidade'],
      ['PK id_auditoria','id_registro (sem FK)','operacao, usuario, data','JSON anterior e novo']]
    if physical:
        fields[0][0]='PK id'; fields[1][0]='PK id'; fields[6][0]='PK id'
        fields[4]=['PK id','FK id_pet, id_clinica','FK id_veterinario, id_tipo_servico','data_consulta, valor, status']
    paths=[('M155 145V225','1 : N',165,190),('M290 285H350','1 : N',297,272),
      ('M485 145V225','1 : N',495,190),('M815 145V185H540V225','1 : N',635,175),
      ('M485 435V355','1 : N',495,407),('M155 355V435','1 : N',165,400),
      ('M290 330H320V590H680','audita • sem FK',440,579)]
    result=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 980 625" role="img" aria-label="Relacionamentos centrais do ClyvoVet">',
      '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#46798b"/></marker></defs>']
    for i,(path,label,x,y) in enumerate(paths):
        result.append(f'<path d="{path}" fill="none" stroke="#46798b" stroke-width="2" marker-end="url(#arrow)"'+(' stroke-dasharray="6 4"' if i==6 else '')+'/>'
            +f'<text x="{x}" y="{y}" fill="#315c70" font-family="Arial" font-size="13">{label}</text>')
    for i,(name,(x,y)) in enumerate(zip(names,pos)):
        result.append(f'<rect x="{x}" y="{y}" width="270" height="130" rx="8" fill="#f1f7f8" stroke="#bfd2db"/>'
          +f'<path d="M{x+8},{y}H{x+262}Q{x+270},{y} {x+270},{y+8}V{y+35}H{x}V{y+8}Q{x},{y} {x+8},{y}" fill="#173b50"/>'
          +f'<text x="{x+12}" y="{y+23}" fill="white" font-family="Arial" font-size="14" font-weight="bold">{mapping[i] if physical else name}</text>')
        for j,f in enumerate(fields[i]): result.append(f'<text x="{x+12}" y="{y+57+j*19}" fill="#203344" font-family="Arial" font-size="13">{esc(f)}</text>')
    return ''.join(result)+'</svg>'

logical=diagram(); physical=diagram(True)
(DOC/'2TDSPF_2026_Modelo_Logico.svg').write_text(logical,encoding='utf-8')
(DOC/'2TDSPF_2026_Modelo_Fisico.svg').write_text(physical,encoding='utf-8')
relationships=[
 ('Tutor → Pet','1 : N','Cada pet tem um tutor obrigatório.'),
 ('Clínica → Pet principal','0..1 : N','Clínica principal é opcional no pet.'),
 ('Pet → Atendimento','1 : N','Cada atendimento possui um pet.'),
 ('Clínica → Atendimento','1 : N','Cada atendimento ocorre em uma clínica.'),
 ('Veterinário → Atendimento','1 : N','FK obrigatória; catálogo validado pelo package.'),
 ('Tipo de serviço → Atendimento','1 : N','FK obrigatória; classificação compatível com o Java.'),
 ('Pet → Leitura de sensor','1 : N','As leituras alimentam o cálculo aprovado da Sprint 3.'),
 ('Pet ⇢ Auditoria','Referência histórica','Sem FK: a trilha deve sobreviver ao DELETE do pet.'),
 ('Pet → Evento de saúde','1 : N','Consulta de origem opcional.'),
 ('Pet → Vacina','1 : N','Clínica da aplicação opcional.'),
 ('Pet → Medicamento','1 : N','Consulta de origem opcional.'),
 ('Tutor → Usuário','0..1 : N','Usuário pode ser vinculado a um tutor.'),
 ('Usuário ↔ Perfil','N : N','Associação TB_USUARIO_PERFIL com PK composta.')]
logical_pages=[page('Modelo lógico relacional',
 '<p>Continuidade do modelo aprovado com nota 100. O núcleo clínico conserva tutores, pets, clínicas, veterinários, serviços, atendimentos, sensores e auditoria. A evolução incorpora autenticação e acompanhamento clínico já utilizados pelo backend Java.</p>'+logical+
 '<p class="small">O diagrama apresenta o núcleo do domínio. As relações adicionais de cuidado e acesso estão detalhadas na página seguinte. A auditoria usa uma referência histórica, não uma chave estrangeira.</p>', 'MODELO LÓGICO'),
 page('Relacionamentos e integridade',table(['Relacionamento','Cardinalidade','Regra'],relationships)+
 '<h3>Dependências e compatibilidade</h3><p>Veterinário e serviço são entidades próprias, com FKs reais no atendimento. Os campos textuais veterinario e tipo_consulta continuam presentes por compatibilidade com o Java existente. O trigger valida o catálogo e impede uma associação contraditória. Essa redundância controlada está explicitada no modelo físico.</p>', 'MODELO LÓGICO')]

sql='\n'.join((ROOT/'sql'/name).read_text(encoding='utf-8') for name in ['01_estrutura.sql','05_integracao_database.sql','06_evolucao_modelo.sql'])
tables={}
for match in re.finditer(r'CREATE TABLE\s+(\w+)\s*\(',sql,re.I):
    i=match.end(); start=i; level=1; quote=False
    while i<len(sql) and level:
        ch=sql[i]
        if ch=="'":
            if quote and i+1<len(sql) and sql[i+1]=="'": i+=2; continue
            quote=not quote
        if not quote:
            if ch=='(': level+=1
            elif ch==')': level-=1
        i+=1
    body=sql[start:i-1]
    parts=[]; level=0; mark=0; quote=False
    for j,ch in enumerate(body):
        if ch=="'": quote=not quote
        if not quote:
            if ch=='(':level+=1
            if ch==')':level-=1
            if ch==',' and level==0:parts.append(body[mark:j]);mark=j+1
    parts.append(body[mark:])
    fields=[]
    for part in parts:
        part=' '.join(part.split())
        if re.match(r'(?i)^(constraint|primary|foreign|unique|check)\b',part): continue
        m=re.match(r'(\w+)\s+((?:number|varchar2|timestamp|date|clob)(?:\([^)]*\))?)(.*)',part,re.I)
        if m:
            col,typ,rest=m.groups(); flags=[]
            if 'NOT NULL' in rest.upper():flags.append('NOT NULL')
            if 'IDENTITY' in rest.upper():flags.append('IDENTITY / PK')
            if 'PRIMARY KEY' in rest.upper():flags.append('PK')
            if 'REFERENCES' in rest.upper():flags.append('FK')
            fields.append([col,typ.upper(),', '.join(flags) or 'Opcional / ver constraints'])
    tables[match.group(1).upper()]=fields
tables['TB_CONSULTA'].extend([['motivo_cancelamento','VARCHAR2(300)','Opcional'],['id_veterinario','NUMBER(6)','FK / NOT NULL'],['id_tipo_servico','NUMBER(6)','FK / NOT NULL']])
tables['CV4_AUD_PET'].extend([['nome_tabela','VARCHAR2(30)','NOT NULL / default TB_PET'],['usuario_so','VARCHAR2(100)','Opcional'],['maquina','VARCHAR2(100)','Opcional'],['usuario_aplicacao','VARCHAR2(100)','Opcional']])
foreign_keys=[]
for source,target in [('TB_USUARIO','TB_TUTOR'),('TB_USUARIO_PERFIL','TB_USUARIO'),('TB_USUARIO_PERFIL','TB_PERFIL'),('TB_PET','TB_TUTOR'),('TB_PET','TB_CLINICA'),('TB_CONSULTA','TB_PET'),('TB_CONSULTA','TB_CLINICA'),('TB_CONSULTA','CV4_VETERINARIO'),('TB_CONSULTA','CV4_TIPO_SERVICO'),('CV4_LEITURA_SENSOR','TB_PET'),('TB_EVENTO_SAUDE','TB_PET'),('TB_EVENTO_SAUDE','TB_CONSULTA'),('TB_VACINA','TB_PET'),('TB_VACINA','TB_CLINICA'),('TB_MEDICAMENTO','TB_PET'),('TB_MEDICAMENTO','TB_CONSULTA')]:foreign_keys.append((source,target))
physical_pages=[page('Modelo físico Oracle',
 '<p>Banco Oracle 19c ou superior. O backend JPA utiliza TB_*; os complementos CV4_* preservam os objetos da Sprint 3 existentes no mesmo schema FIAP. As views não armazenam cópias dos dados.</p>'+physical+
 table(['Entidade anterior','Objeto atual','Origem compartilhada'],[
 ('CLINICA','CV4_CLINICA (view)','TB_CLINICA'),('TUTOR','CV4_TUTOR (view)','TB_TUTOR'),('PET','CV4_PET (view)','TB_PET'),
 ('ATENDIMENTO','CV4_ATENDIMENTO (view)','TB_CONSULTA'),('VETERINARIO','CV4_VETERINARIO','Tabela'),('TIPO_SERVICO','CV4_TIPO_SERVICO','Tabela'),
 ('LEITURA_SENSOR','CV4_LEITURA_SENSOR','Tabela / FK TB_PET'),('AUD_PET','CV4_AUD_PET','Tabela / histórico')]),'MODELO FÍSICO')]
groups=[['TB_TUTOR','TB_CLINICA'],['TB_PET','TB_CONSULTA'],['CV4_VETERINARIO','CV4_TIPO_SERVICO','CV4_LEITURA_SENSOR'],
 ['CV4_AUD_PET','TB_EVENTO_SAUDE'],['TB_VACINA','TB_MEDICAMENTO'],['TB_USUARIO','TB_PERFIL','TB_USUARIO_PERFIL']]
for i,group in enumerate(groups,1):
    content=''
    for name in group: content+=f'<h3>{name}</h3>'+table(['Coluna','Tipo Oracle','Regras'],tables[name],'schema')
    physical_pages.append(page(f'Dicionário físico / {i:02}',content,'MODELO FÍSICO'))
physical_pages.append(page('Chaves, índices e regras',table(['Tabela de origem','Tabela referenciada'],foreign_keys)+
 '<p><b>PKs:</b> coluna id nas tabelas TB_*, id_veterinario, id_tipo_servico, id_leitura e id_auditoria nos complementos; TB_USUARIO_PERFIL usa (id_usuario,id_perfil).</p>'
 '<p><b>Unicidade:</b> username, descrição do perfil, CPF e email do tutor, CNPJ da clínica, microchip do pet, CRMV e nome normalizado do veterinário.</p>'
 '<p><b>Índices:</b> pet/tutor, consulta/pet/data, consulta/status, consulta/veterinário, consulta/serviço, vacina/pet, medicamento/pet, evento/pet, leitura/pet/data e auditoria/registro/data.</p>'
 '<p><b>CHECKs de sensores:</b> temperatura 20–50, frequência 1–400, SpO₂ e atividade 0–100. Auditoria aceita INSERT, UPDATE e DELETE. Essas faixas são validações de entrada da demonstração.</p>'
 '<p><b>Geração de IDs:</b> IDENTITY nas tabelas do Java e auditoria; CV4_SEQ_LEITURA para leituras. Após a carga com IDs explícitos, START WITH LIMIT VALUE sincroniza as identidades.</p>', 'MODELO FÍSICO'))

cover='<section class="page cover"><div class="eyebrow">FIAP / 2TDSPF / 2026</div><div class="rule"></div><h1>ClyvoVet<br>Banco de dados<br>Sprint 4</h1><p class="muted">Mastering Relational and Non-Relational Database</p><p class="pill">Continuação da Sprint 3 • Nota anterior: 100</p><h3>Integrantes</h3>'+table(['Nome','RM'],TEAM)+'<div class="callout">Modelagem relacional • Packages PL/SQL • Integração Java<br>Exportação JSON • Estrutura e importação MongoDB</div><p>Entrega: <b>04 de novembro de 2026</b></p><p class="small muted">A documentação descreve o código entregue. Evidências externas só são consideradas concluídas depois da execução real no Oracle FIAP e no MongoDB.</p></section>'
technical=[page('Continuidade e decisões',
 '<p>O feedback anterior foi “parabéns”, com nota 100. Não existem correções apontadas a aplicar. A evolução conserva as finalidades das duas funções, dos dois procedimentos e da auditoria aprovados; acrescenta organização modular e contratos utilizáveis pelo backend.</p>'+table(['Decisão','Justificativa'],[
 ('Oracle como origem','Preserva PL/SQL e packages da entrega anterior.'),('TB_* e views CV4_*','Java e procedures consultam as mesmas linhas; objetos antigos são preservados.'),
 ('JSON manual','Conserva o algoritmo aprovado; completa o escape de controles.'),('OUT CLOB','Permite ao JDBC obter relatórios e JSON sem capturar DBMS_OUTPUT.'),
 ('Exceções propagadas','A aplicação consegue distinguir erro de um resultado válido.'),('Transação no chamador','Não há COMMIT nos packages; auditoria acompanha a alteração.'),
 ('MongoDB documental','Dataset por atendimento com entidades relacionadas aninhadas.')])+
 '<h3>Compatibilidade explicitada</h3><p>Os nomes físicos evoluíram para os usados no Java, com views CV4_ para leitura pelas rotinas. CACHORRO é apresentado como CAO; CONCLUIDA como REALIZADO. O score Java por regras e o score Oracle por sensores permanecem cálculos distintos.</p>'),
 page('Empacotamento e contratos',table(['Objeto','Contrato / finalidade'],[
 ('PKG_CLYVO_JSON','FN_MONTA_JSON, FN_VALOR, FN_NUMERO e PRC_IMPRIME_CLOB.'),
 ('PKG_CLYVO_CLINICO','FN_CALC_RISCO_PET, PRC_CATALOGOS e PRC_REGISTRAR_LEITURA.'),
 ('PKG_CLYVO_RELATORIOS','PRC_ATENDIMENTOS_JSON e PRC_FATURAMENTO_CLINICA, ambos com OUT CLOB.'),
 ('PKG_CLYVO_AUDITORIA','Serialização completa do pet e persistência da trilha.'),
 ('PKG_CLYVOVET','Fachada pública compatível com as chamadas JDBC do Java.'),
 ('TRG_CV4_AUD_PET','AFTER INSERT/UPDATE/DELETE; delega a auditoria ao package.'),
 ('TRG_CV4_CONSULTA_CAT','BEFORE INSERT/UPDATE; valida e preenche as FKs de catálogo.')])+
 '<div class="callout">Triggers são objetos independentes no Oracle. O empacotamento solicitado é atendido mantendo o disparador fino e concentrando a lógica reutilizável dentro dos packages.</div>'
 '<h3>Exemplo real de chamada do backend</h3><pre>{call PKG_CLYVOVET.PRC_ATENDIMENTOS_JSON(?,?)}\n{call PKG_CLYVOVET.PRC_FATURAMENTO_CLINICA(?,?)}\n{call PKG_CLYVOVET.PRC_REGISTRAR_LEITURA(?,?,?,?,?,?,?)}\n{? = call PKG_CLYVOVET.FN_CALC_RISCO_PET(?)}</pre>'),
 page('Exceções e transações',table(['Código Oracle','Situação tratada'],[
 ('-20001 / -20002','Identificador de clínica inválido / clínica inexistente.'),('-20003 / -20004','Ano inválido / conversão do dataset inválida.'),
 ('-20011 a -20015','Parâmetros JSON, listas divergentes, tipo, valor/tamanho e separador reservado.'),
 ('-20021 a -20024','Pet inválido, inexistente, sem leituras ou espécie sem suporte ao score.'),
 ('-20025 a -20028','Catálogo obrigatório, incompatível, inexistente ou ambíguo.'),
 ('-20029 a -20031','Dispositivo/pet inválido e leitura fora dos limites.'),('-20051 / -20052','Falha de auditoria / operação inválida.'),
 ('-20901 a -20903 / -20990','Instalação protegida, compilação, catálogo inconsistente e assertiva de teste.')])+
 '<p>As falhas de negócio são convertidas por RAISE_APPLICATION_ERROR. Erros inesperados são propagados; não são transformados silenciosamente em sucesso, NULL ou score -1. O backend mostra mensagens de uso sem expor SQL ou credenciais.</p>'
 '<p>Uma clínica existente sem atendimentos retorna []. Um ano sem movimento retorna total zero. Esses dois casos são resultados vazios válidos. Essa evolução em relação à Sprint 3 está documentada.</p>'
 '<p>A auditoria usa valores OLD/NEW escalares e não consulta TB_PET no trigger. O teste transacional valida INSERT, UPDATE, DELETE e desfaz suas alterações ao terminar. Não há transação autônoma na auditoria.</p>'),
 page('Integração Java e dados compartilhados',
 '<p>O perfil oracle utiliza um único DataSource para JPA e JdbcTemplate. As telas existentes persistem em TB_CLINICA, TB_TUTOR, TB_PET e TB_CONSULTA. As views CV4_ consultam essas mesmas linhas para os relatórios PL/SQL.</p>'
 '<p>O administrador usa /relatorios para exportar o JSON e consultar faturamento. Em /relatorios/oracle registra leituras, chama a função de risco e consulta a auditoria. O agendamento no Oracle oferece os veterinários cadastrados no catálogo.</p>'
 + table(['Arquivo Java','Responsabilidade'],[
 ('RelatorioOracleService.java','CallableStatement com parâmetros vinculados e retorno OUT CLOB.'),
 ('OracleClinicoService.java','Procedure de inserção de leituras e função de risco; mesmo DataSource JPA.'),
 ('OracleClinicoController.java','Formulário validado e apresentação dos resultados.'),
 ('CatalogosOracleAdvice.java','Seleção dos veterinários disponíveis no Oracle.'),
 ('application-oracle.properties','Migrations exclusivas db/oracle-sprint4 ou instalação manual.')])+
 '<div class="callout">A versão publicada em PostgreSQL continua disponível, mas não comprova execução de PL/SQL. O vídeo de Database deve usar a aplicação com o perfil Oracle conectado à base FIAP.</div>'
 '<p>A referência usuario_aplicacao da auditoria é opcional: nesta versão, nome_usuario identifica a conta Oracle; não se atribui falsamente esse valor ao login Spring Security.</p>'),
 page('JSON e modelagem MongoDB',
 '<p>O dataset oficial é produzido pela procedure, lendo as seis entidades relacionais. A versão salva deve ser exportada do Oracle real; dados de exemplo escritos manualmente não substituem o entregável.</p>'
 '<pre>atendimentos\n  id_atendimento, data, status, valor\n  clinica: { id, nome, cidade }\n  veterinario: { id, nome, crmv, especialidade }\n  servico: { id, descricao }\n  pet: { id, nome, especie, raca, sexo, peso_kg }\n  tutor: { id, nome }</pre>'
 '<p>Um documento representa um atendimento. Pet, tutor, clínica, veterinário e serviço ficam aninhados porque são consultados junto ao atendimento. Não se acumula um histórico ilimitado dentro do documento do pet.</p>'
 '<p>O MongoDB representa uma projeção dos dados no momento da exportação. Alterar os documentos não atualiza o Oracle. Uma reimportação atualiza os IDs presentes no arquivo; documentos ausentes não são apagados automaticamente.</p>'
 '<p>O importador preserva os campos originais, acrescentando data_bson (UTC) e valor_decimal (Decimal128). O arquivo JSON original não é alterado. O índice único em id_atendimento e o upsert impedem duplicação em reimportações.</p>'
 '<p>O script compara todos os campos de cada documento importado com o arquivo, além da contagem. A coleção usa validação explícita e índices por pet/data e clínica/status/data.</p>'),
 page('Execução reproduzível',
 '<p>Requisitos: JDK 17+, acesso Oracle 19c+ com quota e privilégios de criação de tabelas, views, sequences, packages e triggers; Docker Desktop com engine Linux para o MongoDB.</p>'
 '<pre># Dentro da pasta Database Sprint 4:\n.\\executar-oracle.ps1 check\n.\\executar-oracle.ps1 install\n.\\executar-oracle.ps1 seed\n.\\executar-oracle.ps1 test\n.\\executar-oracle.ps1 export\n.\\executar-mongodb.ps1 iniciar\n.\\executar-mongodb.ps1 importar\n.\\executar-mongodb.ps1 consultar\n.\\executar-oracle.ps1 app</pre>'
 '<p>O acesso Oracle é solicitado localmente, com senha oculta, ou lido do .env não versionado. O executor Java procura o driver JDBC que já acompanha as dependências do backend.</p>'
 '<p>O instalador verifica a existência dos objetos desta versão e interrompe antes de sobrescrever um projeto existente. Não executa DROP nem modifica os objetos da Sprint 3. A instalação manual e o Flyway são alternativas: não misturar os históricos no mesmo schema.</p>'
 '<p>O Oracle faz commits implícitos em DDL. Uma falha de instalação pode deixar objetos parcialmente criados; não há promessa de rollback completo do instalador. Corrigir a causa e revisar os objetos antes de repetir.</p>'
 '<p>O MongoDB fica vinculado a 127.0.0.1, com volume persistente de demonstração. O comando parar mantém os dados. Não se utiliza --drop nem remoção automática de volumes.</p>'),
 page('Validação e evidências',
 '<p>Separar o que foi verificado localmente do que depende de serviços externos é essencial. O arquivo docs/VALIDACAO.md registra o estado atual. Não apresentar saídas esperadas como prints reais.</p>'
 + table(['Verificação','Evidência necessária'],[
 ('Packages e triggers','USER_ERRORS vazio e USER_OBJECTS com status VALID.'),('Mesma base Java/Oracle','Inserir pela interface e consultar o mesmo ID em TB_* e nas views CV4_.'),
 ('Procedures no backend','Mostrar o resultado da exportação, faturamento e inserção de leitura pela aplicação.'),
 ('Carga aprovada','34 atendimentos; 30 realizados em 2026; faturamento R$ 15.635,00 antes de novas operações.'),
 ('Auditoria','OLD/NEW e operação corretos; rollback transacional conferido.'),('JSON real','Arquivo exportado do package e validado como array JSON.'),
 ('MongoDB','Importação, comparação dos campos, contagem e reimportação sem duplicatas.'),('Vídeo','Narração audível e sequência completa sem erros não tratados.')])+
 '<p>Os testes Java de contrato conferem os parâmetros JDBC e a propagação de falhas. Os testes H2 cobrem a aplicação existente. Nenhum deles substitui compilação e execução reais em Oracle.</p>'
 '<p>Os erros de negócio são provocados apenas nos testes controlados, com código esperado e rollback. No vídeo, usar o fluxo principal validado; não gravar uma instalação com falhas.</p>'),
 page('Roteiro do vídeo narrado',table(['Trecho sugerido','Ação e fala principal'],[
 ('0:00–0:45','Apresentar ClyvoVet, integrantes e continuidade da Sprint 3.'),
 ('0:45–1:30','Mostrar modelo lógico/físico e como Java e procedures compartilham TB_*.'),
 ('1:30–3:00','Cadastrar pet na aplicação; conferir o registro e a auditoria no Oracle.'),
 ('3:00–4:30','Agendar, iniciar e concluir atendimento; conferir o mesmo ID em TB_CONSULTA e CV4_ATENDIMENTO.'),
 ('4:30–5:30','Registrar leitura pela tela; explicar a chamada da procedure e consultar o score.'),
 ('5:30–6:30','Executar faturamento pela aplicação e mostrar a chamada do package no código.'),
 ('6:30–7:30','Baixar o dataset JSON pela aplicação e mostrar a estrutura aninhada.'),
 ('7:30–9:00','Importar no MongoDB; conferir documentos, consultas, totais e índices.'),
 ('9:00–9:30','Reimportar e conferir ausência de duplicação; encerrar com os entregáveis.')])+
 '<p>Tempos são uma sugestão de gravação; o enunciado fornecido não fixa limite. A narração deve acompanhar as ações: não substituir por música ou texto na tela.</p>'
 '<p>O link final do vídeo só deve ser adicionado depois da gravação e da conferência de acesso pelo professor. O roteiro não equivale ao vídeo entregue.</p>'),
 page('Conferência dos entregáveis e referências',table(['Item do enunciado','Arquivo / comprovação'],[
 ('Modelos lógico e físico + SQL / 20 pontos','2TDSPF_2026_Modelo_Logico.pdf; 2TDSPF_2026_Modelo_Fisico.pdf; SQL integrado e histórico Sprint 3.'),
 ('Empacotamento e exceções / 25 pontos','sql/07_packages_gatilhos.sql, incorporado ao SQL integrado.'),
 ('JSON relacional / 20 pontos','dataset/2TDSPF_2026_Atendimentos.json, após exportação real.'),
 ('MongoDB / 25 pontos','mongodb/01_criar_estrutura.js, 02_importar_validar.js e 03_consultas.js.'),
 ('Vídeo / 10 pontos','Gravação narrada e link acessível, após execução validada.')])+
 '<h3>Referências oficiais</h3><p class="small">Oracle — PL/SQL Packages:<br>https://docs.oracle.com/en/database/oracle/oracle-database/19/lnpls/plsql-packages.html</p>'
 '<p class="small">Oracle — CREATE TRIGGER:<br>https://docs.oracle.com/en/database/oracle/oracle-database/19/lnpls/CREATE-TRIGGER-statement.html</p>'
 '<p class="small">MongoDB — Modelagem:<br>https://www.mongodb.com/docs/manual/data-modeling/best-practices/</p>'
 '<p class="small">MongoDB — Instalação Docker:<br>https://www.mongodb.com/docs/v8.0/tutorial/install-mongodb-community-with-docker/</p>'
 '<p class="small muted">Código produzido com assistência de IA e sujeito à revisão e compreensão da equipe. Não atribuir contribuições individuais não realizadas.</p>')]

validation_file=DOC/'2TDSPF_2026_Validacao.json'
if validation_file.exists():
    validation=json.loads(validation_file.read_text(encoding='utf-8'))
    dataset_validation=validation['dataset']; java_validation=validation['java']
    technical.insert(0,page('Validação técnica executada',
      '<p>Execução real concluída em 01/11/2026 no terminal Windows, com Oracle FIAP, MongoDB local e build completo do backend. O resumo consolidado está em docs/2TDSPF_2026_Validacao.json.</p>'+
      table(['Parte','Resultado comprovado'],[
       ('Oracle 19.3','12 objetos finais VALID: cinco packages com bodies e dois gatilhos. USER_ERRORS vazio.'),
       ('Rotinas e auditoria','Exceções esperadas e testes transacionais aprovados, com rollback das alterações de teste.'),
       ('Dataset real',str(dataset_validation['documentos'])+' atendimentos exportados do package; '+str(dataset_validation['realizados_2026'])+' realizados em 2026; total R$ 15.635,00.'),
       ('MongoDB','34 documentos importados e conferidos campo a campo; reimportação manteve 34 documentos.'),
       ('Java',str(java_validation['executados'])+' testes executados, zero falhas/erros; '+str(java_validation['ignorados'])+' testes opcionais PostgreSQL ignorados.'),
       ('Integração Oracle','Os dois testes OracleIntegracaoTest executaram exportação JSON e faturamento pelo serviço Java real.'),
       ('JAR',java_validation['jar']+' gerado pelo build completo, com o POM de produção.')])+
      '<h3>Integridade do dataset</h3><p class="small">SHA-256: '+esc(dataset_validation['sha256'])+'</p>'+
      '<div class="callout">Pendências de apresentação: conferir cadastro, atendimento e leitura pela interface Oracle; gravar o vídeo narrado e incluir seu link acessível. Os testes de backend não substituem a demonstração visual exigida.</div>'))

document('ClyvoVet — Modelo lógico',logical_pages,'2TDSPF_2026_Modelo_Logico.html')
document('ClyvoVet — Modelo físico',physical_pages,'2TDSPF_2026_Modelo_Fisico.html')
document('ClyvoVet — Projeto de banco de dados Sprint 4',[cover]+logical_pages+physical_pages+technical,'2TDSPF_2026_Proj_BD.html')
(DOC/'dicionario_modelo.json').write_text(json.dumps(tables,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Documentacao gerada: {len(tables)} tabelas; {1+len(logical_pages)+len(physical_pages)+len(technical)} paginas planejadas.')
