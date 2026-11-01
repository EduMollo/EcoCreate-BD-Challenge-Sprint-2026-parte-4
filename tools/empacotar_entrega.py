"""Pacote revisavel, sem credenciais/cache e sem declarar pendencias concluidas."""
from pathlib import Path
import zipfile
import argparse
import runpy
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description='Empacota os arquivos da Sprint 4 sem credenciais.')
parser.add_argument('--video-url', help='Link HTTPS do video narrado, depois da gravacao.')
args=parser.parse_args()
if args.video_url:
    url=urlparse(args.video_url)
    if url.scheme!='https' or not url.hostname or any(c.isspace() for c in args.video_url):
        parser.error('Informe um link HTTPS completo, sem espacos.')
    (ROOT/'docs/VIDEO.md').write_text(
        '# Video narrado - Database Sprint 4\n\nLink: '+args.video_url+'\n\n'
        'Conferir o acesso do professor sem depender do login do proprietario.\n', encoding='utf-8')
dest=ROOT/'entrega/2TDSPF_2026_ClyvoVet_Database_Sprint4.zip'
runpy.run_path(str(ROOT/'tools/atualizar_fechamento.py'))
dest.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as output:
    for path in sorted(ROOT.rglob('*')):
        relative=path.relative_to(ROOT)
        if not path.is_file() or any(p in {'entrega','__pycache__','.git','data','evidencias'} for p in relative.parts):continue
        if path.name.startswith('.env') or path.suffix in {'.png','.pyc'} or path.name.endswith('.preview.json'):continue
        if path.name in {'.gitkeep','.gitignore','dicionario_modelo.json'}:continue
        output.write(path,relative.as_posix())
print(dest)
with zipfile.ZipFile(dest) as package:
    assert package.testzip() is None, 'ZIP corrompido'
    assert all(not Path(n).name.startswith('.env') for n in package.namelist())
if 'https://' not in (ROOT/'docs/VIDEO.md').read_text(encoding='utf-8'):
    print('Parte tecnica empacotada. Falta gravar o video e incluir seu link com --video-url.')
