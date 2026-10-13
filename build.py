import base64,os,re,shutil,sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
s=open('src.html',encoding='utf-8').read()
def d(p,m): return f"data:{m};base64,"+base64.b64encode(open(p,'rb').read()).decode()
s=s.replace('{{GABI}}',d('assets/gabi.jpg','image/jpeg'))
s=re.sub(r'\{\{DEPO(\d)\}\}',lambda m:d(f'assets/depo{m.group(1)}.jpg','image/jpeg'),s)
s=re.sub(r'\{\{S(\d{3})\}\}',lambda m:d(f'assets/s{m.group(1)}.jpg','image/jpeg'),s)
assert '{{' not in s, re.findall(r'\{\{\w+\}\}',s)
# artifact.html: fragmento para o Artifact do Claude (ele monta o <head> sozinho)
open('artifact.html','w',encoding='utf-8').write(s)
# index.html: documento completo para Vercel / GitHub / WordPress
i=s.index('</style>')+len('</style>')
head=s[:i].replace('<meta charset="utf-8">','<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n<meta name="description" content="Aprenda, na prática, a transformar situações comuns do seu dia em conteúdos autorais. Aulas gravadas + caderno digital por R$ 67.">',1)
doc='<!doctype html>\n<html lang="pt-BR">\n<head>\n'+head+'\n</head>\n<body>\n'+s[i:]+'\n</body>\n</html>\n'
open('index.html','w',encoding='utf-8').write(doc); print(len(doc)//1024,'KB')
if len(sys.argv)>1: shutil.copy('index.html',sys.argv[1])
