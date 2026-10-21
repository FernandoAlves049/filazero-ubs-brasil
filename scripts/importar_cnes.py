#!/usr/bin/env python3
"""Converte o ZIP oficial de UBS do CNES em JSONs estáticos por UF para GitHub Pages.
Não contém nem consulta dados pessoais de pacientes.
"""
import json, zipfile, io, csv, re, unicodedata, urllib.request, pathlib, datetime, os
CATALOG="https://dadosabertos.saude.gov.br/api/3/action/package_show?id=unidades-basicas-de-saude-ubs"
def find_source():
    req=urllib.request.Request(CATALOG,headers={"User-Agent":"FilaZero-UBS/1.0"})
    with urllib.request.urlopen(req,timeout=45) as response:
        payload=json.load(response)
    resources=payload.get("result",{}).get("resources",[])
    choices=[]
    for item in resources:
        url=item.get("url","")
        fmt=str(item.get("format") or "").lower()
        if url and ("json" in fmt or url.lower().endswith(".json.zip")):
            choices.append((item.get("last_modified") or item.get("created") or "",url))
    if not choices: raise ValueError("Nenhum recurso JSON disponível no catálogo oficial")
    choices.sort(reverse=True)
    print("Recurso oficial selecionado:",choices[0][1],flush=True)
    return choices[0][1]
OUT=pathlib.Path("dados"); OUT.mkdir(exist_ok=True)
VALID={"AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"}
def norm(s):
    return re.sub(r"[^a-z0-9]","",unicodedata.normalize("NFKD",str(s)).encode("ascii","ignore").decode().lower())
def val(row,*keys):
    indexed={norm(k):v for k,v in row.items()}
    for k in keys:
        v=indexed.get(norm(k))
        if v not in ("",None,"NULL","null","NaN"): return str(v).strip()
    return ""
def items_from_text(content,name):
    content=content.lstrip("\ufeff\n ")
    if name.endswith(".csv"):
        sample=content[:10000]; dialect=csv.Sniffer().sniff(sample,delimiters=";,\t")
        yield from csv.DictReader(io.StringIO(content), dialect=dialect)
        return
    try:
        obj=json.loads(content)
        if isinstance(obj,list): yield from obj
        elif isinstance(obj,dict):
            for key in ("data","dados","results","items","records","estabelecimentos","ubs"):
                v=obj.get(key)
                if isinstance(v,list): yield from v; return
            yield obj
    except json.JSONDecodeError:
        for line in content.splitlines():
            try:
                row=json.loads(line)
                if isinstance(row,dict): yield row
            except json.JSONDecodeError: pass
def coord(row,*keys):
    text=val(row,*keys).replace(",",".")
    try:return float(text)
    except:return None
def normalize(row):
    if not isinstance(row,dict):return
    uf=val(row,"UF","SG_UF","SIGLA_UF","SIGLA_ESTADO","NO_UF").upper()
    city=val(row,"MUNICIPIO","NO_MUNICIPIO","NOME_MUNICIPIO","CIDADE","MUNICÍPIO")
    if uf not in VALID or not city:return
    latitude=coord(row,"NU_LATITUDE","LATITUDE","VL_LATITUDE","CO_LATITUDE","LAT")
    longitude=coord(row,"NU_LONGITUDE","LONGITUDE","VL_LONGITUDE","CO_LONGITUDE","LON")
    if latitude is not None and not -35<=latitude<=6:latitude=None
    if longitude is not None and not -75<=longitude<=-30:longitude=None
    cnes=val(row,"CNES","CO_CNES","CODIGO_CNES","COD_CNES")
    name=val(row,"NO_FANTASIA","NOME_FANTASIA","NOME_ESTABELECIMENTO","NO_ESTABELECIMENTO","NOME","ESTABELECIMENTO")
    if not name:return
    address=" ".join(filter(None,[val(row,"NO_LOGRADOURO","LOGRADOURO","ENDERECO"),val(row,"NU_ENDERECO","NUMERO","NUMERO_ENDERECO")]))
    return dict(id=cnes or name,name=name,city=city,uf=uf,lat=latitude,lon=longitude,cnes=cnes,address=address,neighborhood=val(row,"NO_BAIRRO","BAIRRO"),phone=val(row,"NU_TELEFONE","TELEFONE","TELEFONE1"),source="CNES")
def main():
    src=find_source()
    req=urllib.request.Request(src,headers={"User-Agent":"FilaZero-UBS/1.0 (dados publicos)"})
    with urllib.request.urlopen(req,timeout=180) as res: raw=res.read()
    zs=zipfile.ZipFile(io.BytesIO(raw))
    by_uf={uf:[] for uf in VALID}; seen=set(); total=0
    for name in zs.namelist():
        if not name.lower().endswith((".json",".jsonl",".ndjson",".csv")):continue
        content=zs.read(name).decode("utf-8-sig",errors="replace")
        for row in items_from_text(content,name.lower()):
            item=normalize(row)
            if not item:continue
            key=(item["uf"],item["city"],item["cnes"] or item["name"])
            if key in seen:continue
            seen.add(key); by_uf[item["uf"]].append(item);total+=1
    if total<1000: raise ValueError(f"Arquivo oficial resultou em apenas {total} registros; verificar esquema antes de publicar")
    for uf, rows in by_uf.items():
        (OUT/(uf+".json")).write_text(json.dumps(rows,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    meta={"source":"CNES/Ministério da Saúde","updated_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"count":total,"per_state":{k:len(v) for k,v in by_uf.items()}}
    (OUT/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    print(meta)
if __name__=="__main__":main()
