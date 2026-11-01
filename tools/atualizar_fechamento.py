"""Atualiza o inventario do pacote; preserva a evidencia historica de banco real."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT.parents[1] / 'CS4 JAVA/Projeto-EcoCreate-Java-Challenge-Sprint-2026-parte-4'
dest = ROOT / 'docs/FECHAMENTO-TECNICO.json'
previous = json.loads(dest.read_text(encoding='utf-8')) if dest.exists() else {}
real = json.loads((ROOT / 'docs/2TDSPF_2026_Validacao.json').read_text(encoding='utf-8'))
dataset = ROOT / 'dataset/2TDSPF_2026_Atendimentos.json'
documents = json.loads(dataset.read_text(encoding='utf-8-sig'))
assert documents and len({d['id_atendimento'] for d in documents}) == len(documents)
digest = hashlib.sha256(dataset.read_bytes()).hexdigest()
local_java = JAVA / 'docs/VALIDACAO-TECNICA.json'
java = json.loads(local_java.read_text(encoding='utf-8')) if local_java.exists() else previous.get('java')
commit = previous.get('backend_commit')
try:
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=JAVA, text=True, stderr=subprocess.DEVNULL).strip()
except (OSError, subprocess.CalledProcessError):
    pass
video = (ROOT / 'docs/VIDEO.md').read_text(encoding='utf-8')
result = {
    'fechado_em': datetime.now(timezone(timedelta(hours=-3))).isoformat(),
    'backend_repositorio': 'https://github.com/EduMollo/Projeto-EcoCreate-Java-Challenge-Sprint-2026-parte-4',
    'backend_commit': commit,
    'oracle_mongodb_execucao_real': {
        'validado_em': real['validado_em'], 'objetos_oracle_valid': 12,
        'documentos_importados_na_execucao': real['dataset']['documentos'],
        'reimportacao_sem_duplicatas': real['mongodb']['reimportacao_sem_duplicatas'],
        'evidencia': 'docs/2TDSPF_2026_Validacao.json'
    },
    'dataset_atual': {'arquivo': dataset.name, 'documentos': len(documents), 'sha256': digest,
        'mesmo_arquivo_da_execucao_registrada': digest == real['dataset']['sha256']},
    'java': java,
    'video': 'link_informado_conferir_acesso' if 'https://' in video else 'gravacao_e_link_pendentes',
    'limites': [
        'Nova conexao Oracle pelo agente foi bloqueada pela permissao de rede; preservada a evidencia real anterior.',
        'Os testes MVC da tela Oracle usam contrato substituido e nao sao evidencia de PL/SQL.',
        'A demonstracao Oracle pela interface e a narracao serao gravadas pela equipe.',
        'Se o dataset mudar durante o video, conferir a nova importacao MongoDB e seus resultados.'
    ]
}
dest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print('Fechamento atualizado; documento historico de validacao real preservado.')
