"""Gate da publicação: cobertura, invariantes e cidades exigidas."""
import json
import pathlib
import re

root=pathlib.Path(__file__).resolve().parents[1]
def main():
    meta=json.loads((root/'dados/meta.json').read_text())
    cities=json.loads((root/'dados/municipios.json').read_text())
    total=0; seen=set(); report=[]
    for uf,count in meta['per_state'].items():
        rows=json.loads((root/f'dados/{uf}.json').read_text())
        assert len(rows)==count and count>0, uf
        for r in rows:
            assert r['uf']==uf and r['cnes'] not in seen and re.fullmatch(r'\d{7}',r['cnes'])
            seen.add(r['cnes'])
            assert (r['lat'] is None)==(r['lon'] is None)
            if r['lat'] is not None:
                assert -34<=r['lat']<=6 and -74<=r['lon']<=-28 and r['coordinate_status']=='validada_malha_ibge'
        total+=len(rows)
    assert total==meta['count'] and total>=30000 and len(cities)>=5500 and len(meta['per_state'])==27
    for name,uf in [('Morrinhos','GO'),('Goiânia','GO'),('Caldas Novas','GO'),('Brasília','DF'),('São Paulo','SP')]:
        rows=[r for r in json.loads((root/f'dados/{uf}.json').read_text()) if r['city']==name]
        assert rows and any(r['lat'] is not None for r in rows), name
        report.append(dict(city=name,uf=uf,count=len(rows),mapped=sum(r['lat'] is not None for r in rows),list_only=sum(r['lat'] is None for r in rows),example_cnes=rows[0]['cnes']))
    path=root/'docs/evidencias/dados.json';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(dict(imported_at=meta['updated_at'],sha256=meta['sha256'],total=total,cities=report),ensure_ascii=False,indent=2))
    print(path.read_text())
if __name__=='__main__':main()
