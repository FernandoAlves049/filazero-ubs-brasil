#!/usr/bin/env python3
"""Importação oficial, sem pacientes; publicação somente após validação completa."""
import argparse
import collections
import datetime
import gzip
import hashlib
import io
import json
import math
import pathlib
import re
import shutil
import tempfile
import time
import unicodedata
import urllib.error
import urllib.request
import zipfile

PORTAL = 'https://dadosabertos.saude.gov.br/dataset/unidades-basicas-de-saude-ubs'
SOURCE = 'https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/CNES/Unidades_Basicas_Saude-UBS_json.zip'
MUNICIPALITIES = 'https://servicodados.ibge.gov.br/api/v1/localidades/municipios'
MESH = 'https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=municipio'
UF_CODES = dict(zip('11 12 13 14 15 16 17 21 22 23 24 25 26 27 28 29 31 32 33 35 41 42 43 50 51 52 53'.split(), 'RO AC AM RR PA AP TO MA PI CE RN PB PE AL SE BA MG ES RJ SP PR SC RS MS MT GO DF'.split()))


def download(url):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'FilaZero-UBS/2.0', 'Accept-Encoding': 'identity'})
            with urllib.request.urlopen(req, timeout=120) as response:
                raw = response.read(100_000_001)
                if len(raw) > 100_000_000:
                    raise ValueError('Download excedeu 100 MB')
                return gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f'Tentativa {attempt + 1}/3: {url}: {exc}', flush=True)
            if isinstance(exc, urllib.error.HTTPError) and exc.code in (400, 401, 403, 404):
                raise
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def find_source():
    # O portal é Next.js, não expõe CKAN em /api/3/action (404).
    try:
        html = download(PORTAL).decode('utf-8')
        match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
        resources = json.loads(match[1])['props']['pageProps']['resources']
        choices = [r for r in resources if r.get('format', '').upper() == 'JSON' and r.get('url', '').startswith('https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/CNES/')]
        chosen = max(choices, key=lambda r: r.get('last_modified') or '')
        return chosen['url'], chosen.get('last_modified'), 'portal'
    except (ValueError, KeyError, TypeError, urllib.error.URLError, OSError) as exc:
        print(f'AVISO: catálogo indisponível ({exc}); usando recurso oficial conhecido: {SOURCE}', flush=True)
        return SOURCE, None, 'recurso oficial fixo; catálogo indisponível'


def norm(value):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode().lower())


def clean(value):
    return '' if value is None else ' '.join(str(value).split())


def number(value):
    try:
        result = float(clean(value).replace(',', '.'))
        return result if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None


def municipality_index(rows):
    result = {}
    for row in rows:
        code = str(row['id'])
        uf = UF_CODES[code[:2]]
        result[code[:6]] = dict(id=code, name=row['nome'], uf=uf)
    if len(result) < 5500:
        raise ValueError('Catálogo IBGE incompleto')
    return result


def ring_contains(x, y, ring):
    inside = False
    for a, b in zip(ring, ring[1:] + ring[:1]):
        if (a[1] > y) != (b[1] > y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            inside = not inside
    return inside


def contains(geometry, lon, lat):
    polygons = [geometry['coordinates']] if geometry['type'] == 'Polygon' else geometry['coordinates']
    return any(ring_contains(lon, lat, p[0]) and not any(ring_contains(lon, lat, hole) for hole in p[1:]) for p in polygons)


def normalize(row, municipalities, geometries):
    code = clean(row.get('IBGE'))[:6]
    # CNES ainda traz o código legado 530040 (Ceilândia), no DF.
    original_code = code
    if code == '530040' and clean(row.get('UF')) == '53':
        code = '530010'
    city = municipalities.get(code)
    if not city:
        raise ValueError(f'Município IBGE desconhecido: {code!r}')
    uf = UF_CODES.get(clean(row.get('UF')), clean(row.get('UF')).upper())
    if uf != city['uf']:
        raise ValueError(f'UF divergente para {code}: {uf}')
    cnes = clean(row.get('CNES')).zfill(7)
    if not re.fullmatch(r'\d{7}', cnes) or cnes == '0000000':
        raise ValueError('CNES/nome inválido')
    lat, lon = number(row.get('LATITUDE')), number(row.get('LONGITUDE'))
    status = 'ausente'
    if lat is not None and lon is not None:
        status = 'fora_do_municipio'
        if -34 <= lat <= 6 and -74 <= lon <= -28:
            geometry = geometries.get(city['id'])
            if geometry and contains(geometry, lon, lat):
                status = 'validada_malha_ibge'
    if status != 'validada_malha_ibge':
        lat = lon = None
    return dict(id=cnes, cnes=cnes, name=clean(row['NOME']) or f'Estabelecimento CNES {cnes} (nome não informado)', city=city['name'], city_id=city['id'], source_city_code=original_code, uf=uf,
                address=clean(row.get('LOGRADOURO')), neighborhood=clean(row.get('BAIRRO')),
                lat=lat, lon=lon, coordinate_status=status, source='CNES')


def build(raw, municipalities_raw, mesh_raw, output, source, modified, discovery):
    municipalities = municipality_index(json.loads(municipalities_raw))
    mesh = json.loads(mesh_raw)
    geometries = {str(f['properties']['codarea']): f['geometry'] for f in mesh['features']}
    if len(geometries) < 5500:
        raise ValueError('Malha municipal incompleta')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith('.json')]
        if len(names) != 1 or archive.getinfo(names[0]).file_size > 100_000_000:
            raise ValueError('ZIP oficial com estrutura inesperada')
        records = json.loads(archive.read(names[0]).decode('utf-8-sig'))
    required = {'CNES', 'UF', 'IBGE', 'NOME', 'LOGRADOURO', 'BAIRRO', 'LATITUDE', 'LONGITUDE'}
    if not isinstance(records, list) or not records or not required <= records[0].keys():
        raise ValueError('Esquema oficial mudou; publicação interrompida')
    by_uf = {uf: [] for uf in sorted(UF_CODES.values())}
    seen, statuses = {}, collections.Counter()
    for row in records:
        item = normalize(row, municipalities, geometries)
        if item['cnes'] in seen:
            if seen[item['cnes']] != item:
                raise ValueError(f"CNES duplicado conflitante: {item['cnes']}")
            continue
        seen[item['cnes']] = item
        by_uf[item['uf']].append(item)
        statuses[item['coordinate_status']] += 1
    total = len(seen)
    if total < 30000 or any(not rows for rows in by_uf.values()):
        raise ValueError(f'Base incompleta: {total} unidades')
    previous = output / 'meta.json'
    if previous.exists() and total < json.loads(previous.read_text())['count'] * .85:
        raise ValueError('Queda superior a 15% na base; revisão humana necessária')
    counts = collections.Counter(item['city_id'] for item in seen.values())
    meta = dict(source='CNES/Ministério da Saúde', source_url=source, catalog_url=PORTAL,
                source_updated_at=modified, discovery=discovery,
                updated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(), count=total,
                sha256=hashlib.sha256(raw).hexdigest(), source_fields=sorted(required),
                per_state={uf: len(rows) for uf, rows in by_uf.items()}, coordinates=dict(statuses),
                municipality_source=MUNICIPALITIES, geometry_source=MESH,
                coordinate_policy='Coordenadas originais CNES dentro da malha municipal simplificada IBGE; sem geocodificação ou posições estimadas.')
    # Todos os registros e arquivos são preparados antes de substituir a saída.
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as tmp:
        stage = pathlib.Path(tmp)
        for uf, rows in by_uf.items():
            rows.sort(key=lambda r: (r['city'], r['name'], r['cnes']))
            (stage / f'{uf}.json').write_text(json.dumps(rows, ensure_ascii=False, separators=(',', ':'), allow_nan=False), encoding='utf-8')
        cities = [dict(**c, count=counts[c['id']]) for c in municipalities.values()]
        (stage / 'municipios.json').write_text(json.dumps(cities, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        (stage / 'meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
        output.mkdir(exist_ok=True)
        for file in stage.iterdir():
            shutil.copy2(file, output / file.name)
    return meta


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=pathlib.Path, default=pathlib.Path('dados'))
    args = parser.parse_args()
    source, modified, discovery = find_source()
    print('Recurso oficial:', source, flush=True)
    raw = download(source)
    municipalities = download(MUNICIPALITIES)
    mesh = download(MESH)
    print(json.dumps(build(raw, municipalities, mesh, args.output, source, modified, discovery), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
