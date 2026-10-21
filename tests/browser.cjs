const { chromium } = require('playwright');
const fs = require('fs');
const assert = require('node:assert/strict');
const base = process.env.TEST_URL || 'http://127.0.0.1:8000/';
const out = process.env.EVIDENCE_DIR || 'docs/evidencias';
fs.mkdirSync(out,{recursive:true});
(async () => {
 const browser = await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const report={url:base,at:new Date().toISOString(),profiles:[]};
 try {
  for (const [profile,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}]]) {
   const context=await browser.newContext({viewport,isMobile:profile==='mobile',hasTouch:profile==='mobile'});
   const page=await context.newPage(), errors=[], remoteMutations=[];
   page.on('pageerror',e=>errors.push(e.message));
   page.on('request',r=>{if(!['GET','HEAD'].includes(r.method()))remoteMutations.push(r.url());});
   await page.goto(base,{waitUntil:'domcontentloaded'});
   await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('unidades do conjunto'),{timeout:60000});
   await page.waitForFunction(()=>typeof map!=='undefined' && map && map.loaded(),{timeout:60000});
   const result={profile,viewport,cities:[],checks:[]};
   for(const [city,uf] of [['Morrinhos','GO'],['Goiania','GO'],['Caldas Novas','GO'],['Brasilia','DF'],['Sao Paulo','SP']]) {
    await page.locator('#city').fill(city); await page.locator('#uf').selectOption(uf);await page.locator('#search').click();
    await page.waitForFunction(()=>!document.querySelector('#search').disabled);
    const state=await page.evaluate(()=>({count:Number(document.querySelector('#count').textContent),cards:document.querySelectorAll('.unit').length,markers:markers.length,status:document.querySelector('#status').textContent,overflow:document.documentElement.scrollWidth>innerWidth,mapLoaded:map.loaded()}));
    assert(state.count>0,state.status); assert.equal(state.count,state.cards);assert(state.markers>0);assert.equal(state.overflow,false);
    const official=await page.evaluate(async uf=>{const rows=await(await fetch(`./dados/${uf}.json`)).json();const name=document.querySelector('#city').value;return rows.filter(r=>r.city===name);},uf);
    assert.equal(state.count,official.length);assert.equal(state.markers,official.filter(r=>r.lat!==null).length);
    result.cities.push({city,uf,...state});
    if(city==='Morrinhos') {
     await page.locator('.unit').first().click();
     await page.screenshot({path:`${out}/${profile}-morrinhos.png`,fullPage:true});
    }
   }
   await page.locator('#city').fill('Cidade inexistente xyz');await page.locator('#search').click();await page.waitForFunction(()=>!document.querySelector('#search').disabled);
   assert.equal(await page.locator('#count').textContent(),'0');assert.match(await page.locator('#status').textContent(),/não encontrado/);result.checks.push('Município inexistente não reutiliza resultados anteriores');
   await page.locator('[data-tab="fila"]').click();
   await page.locator('#cancel').click();assert.equal(await page.locator('#available').textContent(),'1');
   await page.locator('#cancel').click();assert.equal(await page.locator('#available').textContent(),'1');
   await page.locator('[data-confirm]').click();assert.equal(await page.locator('#confirmed').textContent(),'1');assert.match(await page.locator('#slots').textContent(),/Paciente B/);
   for(const time of ['15:00','16:00','17:00']) {await page.locator('#time').fill(time);await page.locator('#cancel').click();await page.locator('[data-confirm]').last().click();}
   assert.equal(await page.locator('#confirmed').textContent(),'3');assert.equal(await page.locator('#waiting').textContent(),'0');assert.match(await page.locator('#simulation-status').textContent(),/Não há mais/);
   await page.screenshot({path:`${out}/${profile}-simulacao.png`,fullPage:true});
   await page.reload();await page.locator('[data-tab="fila"]').click();assert.equal(await page.locator('#confirmed').textContent(),'3');
   await page.locator('[data-tab="painel"]').click();assert.equal(await page.locator('#rate').textContent(),'75%');
   await page.locator('[data-tab="fila"]').click();page.once('dialog',d=>d.accept());await page.locator('#reset').click();assert.equal(await page.locator('#created').textContent(),'0');
   result.checks.push('Vaga, prevenção de duplicidade, prioridade B/A/C, fila esgotada, persistência, indicadores e reset');
   assert.deepEqual(remoteMutations,[]);assert.deepEqual(errors,[]);result.checks.push('Sem erros JavaScript e sem requisições de escrita/pacientes');result.errors=errors;
   report.profiles.push(result);await context.close();
  }
  // Falha externa do mapa não pode impedir lista ou demonstração.
  const context=await browser.newContext();const page=await context.newPage();
  await page.route('**/assets/maplibre-gl.js',r=>r.abort());
  await page.addInitScript(()=>localStorage.setItem('filazero-demo-v2','{"broken":true}'));
  await page.goto(base);await page.waitForFunction(()=>Number(document.querySelector('#count').textContent)>0);
  assert.match(await page.locator('#map-status').textContent(),/indisponível/);await page.locator('[data-tab="fila"]').click();await page.locator('#cancel').click();assert.equal(await page.locator('#available').textContent(),'1');
  report.resilience=['Mapa bloqueado mantém lista e simulação','Estado local inválido recuperado'];
  await context.close();
  const failed=await browser.newPage();await failed.route('**/dados/GO.json',r=>r.fulfill({status:503,body:'unavailable'}));await failed.goto(base);await failed.waitForFunction(()=>!document.querySelector('#search').disabled);assert.match(await failed.locator('#status').textContent(),/503/);assert.equal(await failed.locator('#count').textContent(),'0');await failed.unroute('**/dados/GO.json');await failed.locator('#search').click();await failed.waitForFunction(()=>Number(document.querySelector('#count').textContent)>0);report.resilience.push('HTTP 503 explícito, sem dados inventados, nova tentativa recupera');
  report.result='PASS'; fs.writeFileSync(`${out}/browser.json`,JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
 } catch(error) { report.result='FAIL';report.error=error.stack;fs.writeFileSync(`${out}/browser.json`,JSON.stringify(report,null,2));throw error; }
 finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
