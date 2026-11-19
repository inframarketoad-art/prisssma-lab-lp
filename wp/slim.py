"""Gera wp/cadernob/ (variação leve da LP prisssma.com/caderno) a partir da página que está no ar.

A pasta cadernob/ inteira (index.html + img/) sobe para public_html/ na Hostinger e fica em
prisssma.com/cadernob/ (pasta real: o servidor entrega antes do WordPress).

- As imagens embutidas em base64 viram arquivos WebP em img/, com caminho relativo.
  Abaixo da primeira dobra: loading="lazy".
- Pixel: PageView no carregamento; ViewContent só com engajamento (15 s ou 25% de rolagem);
  CliqueComprar no clique de qualquer botão da Kiwify.
- UTMs e fbclid da URL do anúncio são repassados para o link do checkout.

Uso: python3 -I wp/slim.py <html de origem> <pasta de saída, ex. caderno-b> <variante, ex. B>
"""
import base64, hashlib, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, FOLDER, VARIANT = sys.argv[1], sys.argv[2], sys.argv[3]
PAGE_DIR = os.path.join(ROOT, 'wp', FOLDER)
OUT_DIR = os.path.join(PAGE_DIR, 'img')
BASE_URL = 'img/'
os.makedirs(OUT_DIR, exist_ok=True)
s = open(SRC, encoding='utf-8').read()

# 1) data URIs -> webp
names = {}
def to_file(m):
    uri = m.group(0)
    if uri in names:
        return BASE_URL + names[uri]
    mime, b64 = re.match(r'data:image/([a-z]+);base64,(.+)', uri, re.S).groups()
    raw = base64.b64decode(b64)
    h = hashlib.sha1(raw).hexdigest()[:10]
    with tempfile.NamedTemporaryFile(suffix='.' + mime, delete=False) as t:
        t.write(raw); tmp = t.name
    w = int(re.search(rb'pixelWidth: (\d+)', subprocess.run(['sips', '-g', 'pixelWidth', tmp], capture_output=True).stdout).group(1))
    name = f'{len(names)+1:02d}-{h}.webp'
    cmd = ['cwebp', '-quiet', '-q', '74', '-m', '6', '-mt']
    if w > 1000: cmd += ['-resize', '1000', '0']
    subprocess.run(cmd + [tmp, '-o', os.path.join(OUT_DIR, name)], check=True)
    os.unlink(tmp)
    names[uri] = name
    return BASE_URL + name
s = re.sub(r'data:image/[a-z]+;base64,[A-Za-z0-9+/=]+', to_file, s)

# no celular a barra fixa de compra já aparece; o botão do topo encavalava no logo
s = s.replace('</style>', '@media (max-width:600px){.mini-cta{display:none}}\n</style>', 1)

# 2) imagens abaixo da primeira dobra carregam sob demanda
fold = s.index('<!-- DOR')
def lazy(m):
    tag = m.group(0)
    if 'loading=' in tag: tag = re.sub(r'\sloading="[^"]*"', '', tag)
    return tag[:-1].rstrip('/') + ' loading="lazy" decoding="async">'
s = s[:fold] + re.sub(r'<img\b[^>]*>', lazy, s[fold:])
# primeira dobra: a imagem "depois" do topo é a maior da tela inicial
s = s.replace('<img class="slide" src="' + BASE_URL, '<img class="slide" fetchpriority="high" src="' + BASE_URL, 1)

# 3) pixel
PIXEL = """<!-- Meta Pixel - Prisssma -->
<script>
!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
fbq('init','2236850833905931');
fbq('track','PageView');
/* ViewContent = quem de fato consumiu a página: 15 segundos nela OU rolou 25%.
   É esse evento que a campanha de otimização por visualização de conteúdo deve usar. */
(function(){
  var sent=false, PRODUTO={content_name:'Caderno das Boas Ideias',content_type:'product',content_ids:['caderno-boas-ideias'],value:67,currency:'BRL',lp_variant:'"+VARIANT+"'};
  function vc(motivo){ if(sent) return; sent=true; fbq('track','ViewContent',PRODUTO); }
  setTimeout(function(){ vc('tempo') }, 15000);
  addEventListener('scroll', function(){
    var d=document.documentElement; if((scrollY+innerHeight)/d.scrollHeight>=0.25) vc('rolagem');
  }, {passive:true});
  /* clique em qualquer botão de compra (separa "clicou" de "carregou o checkout" na Kiwify) */
  document.addEventListener('click', function(e){
    var a=e.target.closest && e.target.closest('a[href*="pay.kiwify.com.br"]');
    if(a) fbq('trackCustom','CliqueComprar',{value:67,currency:'BRL',lp_variant:'"+VARIANT+"'});
  });
})();
</script>
<noscript><img height="1" width="1" style="display:none" src="https://www.facebook.com/tr?id=2236850833905931&ev=PageView&noscript=1"/></noscript>
<!-- End Meta Pixel -->"""
PIXEL = PIXEL.replace('"+VARIANT+"', VARIANT)
# remove noindex antigo (é recolocado no topo) e devolve </head><body> se estavam dentro do bloco do pixel
s = s.replace('<meta name="robots" content="noindex">', '')
had_head = '</head>' in re.search(r'<!-- Meta Pixel - Prisssma -->.*?<!-- End Meta Pixel -->', s, re.S).group(0)
s = re.sub(r'<!-- Meta Pixel - Prisssma -->.*?<!-- End Meta Pixel -->', lambda m: PIXEL + ('\n</head>\n<body>' if had_head else ''), s, count=1, flags=re.S)
assert s.count('</head>') == 1 and s.count('<body') == 1
assert "fbq('track','ViewContent',PRODUTO)" in s

# variação não deve competir com /caderno no Google
s = s.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n<meta name="robots" content="noindex">', 1)

# 4) UTMs do anúncio seguem para o checkout da Kiwify
UTM = """<script>
/* repassa utm_*, fbclid e src da URL do anúncio para os links da Kiwify */
(function(){
  var q=new URLSearchParams(location.search), keep=new URLSearchParams();
  q.forEach(function(v,k){ if(/^(utm_|fbclid$|src$|sck$)/.test(k)) keep.set(k,v) });
  if(![...keep].length) return;
  document.querySelectorAll('a[href*="pay.kiwify.com.br"]').forEach(function(a){
    var u=new URL(a.href); keep.forEach(function(v,k){ if(!u.searchParams.has(k)) u.searchParams.set(k,v) }); a.href=u.toString();
  });
})();
</script>
</body>"""
s = s.replace('</body>', UTM, 1)

out = os.path.join(PAGE_DIR, 'index.html')
open(out, 'w', encoding='utf-8').write(s)
total = sum(os.path.getsize(os.path.join(OUT_DIR, n)) for n in set(names.values()))
print(f'{len(names)} imagens -> {FOLDER}/img/ ({total//1024} KB no total)')
print(f'HTML: {len(s.encode())//1024} KB (antes: {os.path.getsize(SRC)//1024} KB)')
