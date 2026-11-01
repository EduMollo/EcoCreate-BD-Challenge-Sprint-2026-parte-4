"""Renderizador PDF vetorial sem dependencias: texto WinAnsi, tabelas e diagramas.

Os HTMLs permanecem como fonte editavel. Nao depende de navegador, rede ou Office.
"""
from pathlib import Path
from html.parser import HTMLParser
import json
import re
import zlib

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs'
W,H=595.28,841.89
M=42

def clean(text):
    return text.replace('→',' > ').replace('⇢',' > ').replace('↔',' / ').replace('₂','2').replace('✓','OK').replace('–','-').replace('—','-').replace('\u00a0',' ')

class Reader(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pages=[]; self.page=None; self.block=None; self.buf=[]; self.rows=None; self.row=None; self.cell=None; self.svg=0; self.diagram_text=[]; self.ignore=0
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag in ('style','title'):self.ignore+=1;return
        if self.ignore:return
        if tag=='svg':self.svg+=1;self.diagram_text=[];return
        if self.svg:return
        if tag=='section':self.page=[];self.pages.append(self.page)
        if self.page is None:return
        if tag=='table':self.rows=[]
        elif tag=='tr' and self.rows is not None:self.row=[]
        elif tag in ('th','td') and self.row is not None:self.cell=[]
        elif tag in ('h1','h2','h3','p','pre') or (tag=='div' and attrs.get('class') in ('eyebrow','callout','footer')):
            self.block=attrs.get('class',tag) if tag=='div' else tag;self.buf=[]
        elif tag=='br':
            if self.cell is not None:self.cell.append('\n')
            elif self.block:self.buf.append('\n')
    def handle_endtag(self,tag):
        if tag in ('style','title') and self.ignore:self.ignore-=1;return
        if self.ignore:return
        if self.svg:
            if tag=='svg':
                self.svg-=1
                self.page.append(('diagram','TB_CONSULTA' in ''.join(self.diagram_text)))
            return
        if tag in ('td','th') and self.cell is not None:
            self.row.append(''.join(self.cell).strip());self.cell=None
        elif tag=='tr' and self.row is not None:
            self.rows.append(self.row);self.row=None
        elif tag=='table' and self.rows is not None:
            self.page.append(('table',self.rows));self.rows=None
        elif self.block and (tag in ('h1','h2','h3','p','pre') or tag=='div'):
            if self.block!='footer':self.page.append((self.block,''.join(self.buf).strip()))
            self.block=None;self.buf=[]
    def handle_data(self,data):
        if self.ignore:return
        if self.svg:self.diagram_text.append(data);return
        if self.cell is not None:self.cell.append(data)
        elif self.block:self.buf.append(data)

def width(text,size):
    # Limite conservador: impede transbordamento mesmo sem bibliotecas de fontes.
    return sum((0.95 if c in 'WM@%' else 0.68 if c.isupper() else 0.60 if c.isdigit() else 0.30 if c in ' il.,:;!|\'`' else 0.57)*size for c in text)

def wrap(text,size,max_width):
    lines=[]
    for para in clean(text).split('\n'):
        line=''
        for word in para.split():
            if width(word,size)>max_width:
                if line:lines.append(line);line=''
                piece=''
                for ch in word:
                    if width(piece+ch,size)>max_width:lines.append(piece);piece=''
                    piece+=ch
                line=piece
            elif line and width(line+' '+word,size)>max_width:lines.append(line);line=word
            else:line=(line+' '+word).strip()
        lines.append(line)
    return lines or ['']

def literal(text):
    data=clean(text).encode('cp1252','replace')
    return '('+''.join('\\'+chr(b) if b in (40,41,92) else chr(b) if 32<=b<127 else f'\\{b:03o}' for b in data)+')'

class PDF:
    def __init__(self,title):self.title=title;self.pages=[];self.ops=[];self.previews=[];self.y=0;self.page_no=0
    def new(self):
        if self.ops:self.finish()
        self.ops=[];self.preview=[];self.y=H-M;self.page_no+=1
    def finish(self):
        self.line(M,32,W-M,32,'#cbd9df')
        self.text(M,20,'ClyvoVet | FIAP 2TDSPF | Sprint 4 | 04/11/2026',8,'#607785')
        self.text(W-M-20,20,str(self.page_no),8,'#607785')
        self.pages.append('\n'.join(self.ops).encode('ascii'));self.previews.append(self.preview);self.ops=[]
    def need(self,height):
        if self.y-height<50:self.new()
    def rgb(self,color):return ' '.join(f'{int(color[i:i+2],16)/255:.3f}' for i in (1,3,5))
    def text(self,x,y,text,size=10,color='#203344',bold=False):
        self.ops.append(f'BT /F{2 if bold else 1} {size} Tf {self.rgb(color)} rg 1 0 0 1 {x:.2f} {y:.2f} Tm {literal(text)} Tj ET')
        self.preview.append(dict(kind='text',x=x,y=H-y,text=clean(text),size=size,color=color,bold=bold))
    def rect(self,x,y,w,h,color):
        self.ops.append(f'{self.rgb(color)} rg {x:.2f} {y:.2f} {w:.2f} {h:.2f} re f')
        self.preview.append(dict(kind='rect',x=x,y=H-y-h,w=w,h=h,color=color))
    def line(self,x1,y1,x2,y2,color='#46798b'):
        self.ops.append(f'{self.rgb(color)} RG 0.7 w {x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S')
        self.preview.append(dict(kind='line',x=x1,y=H-y1,x2=x2,y2=H-y2,color=color))
    def paragraph(self,text,size=10,color='#203344',bold=False,bg=None):
        pad=9 if bg else 0;lines=wrap(text,size,W-2*M-2*pad);lh=size*1.45;height=len(lines)*lh+pad*2+8
        self.need(height)
        if bg:self.rect(M,self.y-height+5,W-2*M,height,bg)
        for line in lines:
            self.text(M+pad,self.y-pad-size,line,size,color,bold);self.y-=lh
        self.y-=pad*2+8
    def table(self,rows):
        if not rows:return
        cols=max(map(len,rows)); ratios={2:[0.44,0.56],3:[0.32,0.27,0.41]}.get(cols,[1/cols]*cols)
        widths=[(W-2*M)*r for r in ratios];font=8.5;lh=12
        def draw(row,header=False,index=0):
            cells=[wrap(str(row[j]) if j<len(row) else '',font,widths[j]-12) for j in range(cols)]
            height=max(map(len,cells))*lh+12
            if self.y-height<50:
                self.new()
                if not header:draw(rows[0],True)
            self.rect(M,self.y-height,W-2*M,height,'#173b50' if header else '#f0f6f7' if index%2 else '#ffffff')
            x=M
            for j,lines in enumerate(cells):
                for k,line in enumerate(lines):self.text(x+6,self.y-12-k*lh,line,font,'#ffffff' if header else '#203344',header)
                x+=widths[j]
            self.y-=height;self.line(M,self.y,W-M,self.y,'#dbe5e9')
        draw(rows[0],True)
        for i,row in enumerate(rows[1:]):draw(row,index=i)
        self.y-=14
    def diagram(self,physical=False):
        scale=(W-2*M)/980;height=625*scale
        self.need(height+10);top=self.y
        def point(x,y):return M+x*scale,top-y*scale
        def segment(points):
            for a,b in zip(points,points[1:]):self.line(*point(*a),*point(*b))
            a,b=points[-2:];dx=b[0]-a[0];dy=b[1]-a[1]
            if abs(dx)>abs(dy):arrow=[(b[0]-(8 if dx>0 else -8),b[1]-4),b,(b[0]-(8 if dx>0 else -8),b[1]+4)]
            else:arrow=[(b[0]-4,b[1]-(8 if dy>0 else -8)),b,(b[0]+4,b[1]-(8 if dy>0 else -8))]
            for a,b in zip(arrow,arrow[1:]):self.line(*point(*a),*point(*b))
        for pts,label,x,y in [([(155,145),(155,225)],'1 : N',165,190), ([(290,285),(350,285)],'1 : N',295,272),
         ([(485,145),(485,225)],'1 : N',495,190), ([(815,145),(815,185),(540,185),(540,225)],'1 : N',635,175),
         ([(485,435),(485,355)],'1 : N',495,407), ([(155,355),(155,435)],'1 : N',165,400),
         ([(290,330),(320,330),(320,590),(680,590),(680,560)],'Auditoria sem FK',440,579)]:
            segment(pts);self.text(*point(x,y),label,7,'#315c70')
        names=['TUTOR','PET','LEITURA_SENSOR','VETERINARIO','ATENDIMENTO','TIPO_SERVICO','CLINICA','AUD_PET']
        physical_names=['TB_TUTOR','TB_PET','CV4_LEITURA_SENSOR','CV4_VETERINARIO','TB_CONSULTA','CV4_TIPO_SERVICO','TB_CLINICA','CV4_AUD_PET']
        fields=[['PK id_tutor','nome, cpf, email'],['PK id_pet','FK id_tutor','nome, especie, peso_kg'],['PK id_leitura','FK id_pet','data_hora, sinais vitais'],
         ['PK id_veterinario','nome, crmv'],['PK id_atendimento','FK pet, clinica','FK veterinario, servico','data, valor, status'],
         ['PK id_tipo_servico','descricao, preco_base'],['PK id_clinica','nome, cidade'],['PK id_auditoria','id_registro (sem FK)','operacao, usuario, data','JSON anterior e novo']]
        if physical:
            fields[0][0]='PK id';fields[1][0]='PK id';fields[6][0]='PK id'
            fields[4]=['PK id','FK id_pet, id_clinica','FK id_veterinario, id_tipo_servico','data_consulta, valor, status']
        for i,(x,y) in enumerate([(20,15),(20,225),(20,435),(350,15),(350,225),(350,435),(680,15),(680,435)]):
            bx,by=point(x,y+130);self.rect(bx,by,270*scale,130*scale,'#eef5f7')
            bx,by=point(x,y+35);self.rect(bx,by,270*scale,35*scale,'#173b50')
            self.text(*point(x+12,y+23),physical_names[i] if physical else names[i],7.3,'#ffffff',True)
            for j,f in enumerate(fields[i]):self.text(*point(x+12,y+57+j*19),f,6.3 if len(f)>31 else 7,'#203344')
        self.y-=height+14
    def save(self,path):
        if self.ops:self.finish()
        objects=[]
        def add(data):objects.append(data if isinstance(data,bytes) else data.encode('ascii'));return len(objects)
        catalog=add('');pages_obj=add('')
        font1=add('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')
        font2=add('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>')
        ids=[]
        for data in self.pages:
            stream=zlib.compress(data)
            content=add(f'<< /Length {len(stream)} /Filter /FlateDecode >>\nstream\n'.encode()+stream+b'\nendstream')
            ids.append(add(f'<< /Type /Page /Parent {pages_obj} 0 R /MediaBox [0 0 {W} {H}] /Resources << /Font << /F1 {font1} 0 R /F2 {font2} 0 R >> >> /Contents {content} 0 R >>'))
        objects[catalog-1]=f'<< /Type /Catalog /Pages {pages_obj} 0 R >>'.encode()
        objects[pages_obj-1]=f'<< /Type /Pages /Count {len(ids)} /Kids [{" ".join(str(i)+" 0 R" for i in ids)}] >>'.encode()
        output=bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n');offsets=[0]
        for i,obj in enumerate(objects,1):offsets.append(len(output));output.extend(f'{i} 0 obj\n'.encode()+obj+b'\nendobj\n')
        start=len(output);output.extend(f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode())
        for offset in offsets[1:]:output.extend(f'{offset:010} 00000 n \n'.encode())
        output.extend(f'trailer\n<< /Size {len(objects)+1} /Root {catalog} 0 R >>\nstartxref\n{start}\n%%EOF\n'.encode())
        path.write_bytes(output)
        # Operacoes da pagina sao exportadas para inspecao visual opcional via GDI.
        (DOC/(path.stem+'.preview.json')).write_text(json.dumps(self.previews,ensure_ascii=False),encoding='utf-8')
        for page in self.previews:
            for op in page:
                if op['kind']=='text' and (op['y']<0 or op['y']>H):raise ValueError('Texto fora da pagina')
        print(path.name+f': {len(ids)} paginas, {len(output)} bytes')

for source in sorted(DOC.glob('2TDSPF_2026_*.html')):
    reader=Reader();reader.feed(source.read_text(encoding='utf-8'))
    pdf=PDF(source.stem)
    for page in reader.pages:
        pdf.new()
        for kind,content in page:
            if kind=='table':pdf.table(content)
            elif kind=='diagram':pdf.diagram(content)
            elif kind=='eyebrow':pdf.paragraph(content,8,'#147d87',True)
            elif kind=='h1':pdf.paragraph(content,30,'#132e45',True)
            elif kind=='h2':pdf.paragraph(content,21,'#132e45',True)
            elif kind=='h3':pdf.paragraph(content,12,'#147d87',True)
            elif kind=='callout':pdf.paragraph(content,10,bg='#eaf5f4')
            elif kind=='pre':pdf.paragraph(content,9,bg='#eef4f6')
            else:pdf.paragraph(content)
    pdf.save(source.with_suffix('.pdf'))
