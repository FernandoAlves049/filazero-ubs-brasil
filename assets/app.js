'use strict';
const $ = id => document.getElementById(id);
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const normalizeName = text => String(text || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim().replace(/\s+/g, ' ');
const STATES = 'AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split(' ');
STATES.forEach(uf => $('uf').add(new Option(uf, uf)));
$('uf').value = 'GO';
let map = null;
let markers = [];
try {
  map = new maplibregl.Map({container:'map', style:'https://tiles.openfreemap.org/styles/liberty', center:[-49.2,-16.7], zoom:6});
  map.addControl(new maplibregl.NavigationControl(), 'top-left');
  map.on('load', () => { $('map-status').textContent = 'Mapa disponível • selecione uma unidade na lista'; });
  map.on('error', () => { $('map-status').textContent = 'Falha ao carregar parte do mapa. A listagem continua disponível.'; });
} catch (error) {
  $('map-status').textContent = 'Mapa indisponível neste navegador. Use a listagem de unidades abaixo.';
}
const notice = text => { $('simulation-status').textContent = text; };
const start = () => ({patients:[{name:'Paciente A',priority:2,days:4,done:false},{name:'Paciente B',priority:1,days:7,done:false},{name:'Paciente C',priority:3,days:3,done:false}],slots:[],log:[]});
const STORAGE = 'filazero-demo-v2';
function validState(state) {
  return state && Array.isArray(state.patients) && state.patients.length === 3 &&
    state.patients.every((p,i) => p.name === ['Paciente A','Paciente B','Paciente C'][i] && typeof p.done === 'boolean' && p.priority === [2,1,3][i] && p.days === [4,7,3][i]) &&
    Array.isArray(state.slots) && state.slots.length <= 200 && state.slots.every(s => typeof s.unit === 'string' && typeof s.done === 'boolean' && /^\d{4}-\d{2}-\d{2}$/.test(s.date) && /^\d{2}:\d{2}$/.test(s.time) && (!s.done || ['Paciente A','Paciente B','Paciente C'].includes(s.patient))) &&
    Array.isArray(state.log) && state.log.length <= 400 && state.log.every(s => typeof s === 'string');
}
let data = start();
try { const saved = JSON.parse(localStorage.getItem(STORAGE)); if (validState(saved)) data = saved; } catch (_) { notice('Armazenamento indisponível. A demonstração funciona nesta sessão.'); }
function save() { try { localStorage.setItem(STORAGE, JSON.stringify(data)); } catch (_) { notice('Demonstração atualizada nesta sessão; o navegador não permitiu salvar.'); } }
function render() {
  const done = data.slots.filter(s => s.done).length;
  $('available').textContent = data.slots.length - done;
  $('waiting').textContent = data.patients.filter(p => !p.done).length;
  $('confirmed').textContent = $('reused').textContent = done;
  $('created').textContent = data.slots.length;
  $('rate').textContent = (data.slots.length ? Math.round(done / data.slots.length * 100) : 0) + '%';
  $('patients').innerHTML = data.patients.map(p => `<div class="cardrow"><b>${p.name}</b><small>Prioridade ilustrativa: ${p.priority} | ${p.days} dias de espera | ${p.done ? 'Confirmado' : 'Aguardando'}</small></div>`).join('');
  $('slots').innerHTML = data.slots.map((s,i) => `<div class="cardrow"><b>${escapeHtml(s.unit)}</b><small>${escapeHtml(s.date)} às ${escapeHtml(s.time)} | ${s.done ? 'Confirmada para ' + escapeHtml(s.patient) : 'Liberada'}</small>${s.done ? '' : `<button class="primary" data-confirm="${i}">Simular convocação</button>`}</div>`).join('') || '<p class="muted">Ainda não há vagas liberadas.</p>';
  $('log').innerHTML = data.log.slice().reverse().map(text => `<div class="cardrow">${escapeHtml(text)}</div>`).join('') || '<p class="muted">Nenhuma movimentação.</p>';
  document.querySelectorAll('[data-confirm]').forEach(button => button.onclick = () => {
    const slot = data.slots[Number(button.dataset.confirm)];
    if (!slot || slot.done) return;
    const patient = data.patients.filter(p => !p.done).sort((a,b) => a.priority - b.priority || b.days - a.days)[0];
    if (!patient) return notice('Não há mais pacientes fictícios aguardando. Reinicie a demonstração para repetir.');
    patient.done = true; slot.done = true; slot.patient = patient.name;
    data.log.push(`SIMULAÇÃO: vaga ${slot.date} ${slot.time} atribuída a ${patient.name}.`);
    notice('Convocação simulada. Nenhuma mensagem foi enviada.'); save(); render();
  });
}
const today = new Date();
const localDate = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;
$('date').value = $('date').min = localDate;
$('cancel').onclick = () => {
  const date = $('date').value, time = $('time').value, unit = $('selectedunit').value;
  if (!date || !time || !$('date').checkValidity() || !$('time').checkValidity()) return notice('Informe uma data a partir de hoje e um horário válido.');
  if (data.slots.some(s => s.unit === unit && s.date === date && s.time === time)) return notice('Já existe uma vaga demonstrativa nesta unidade, data e horário.');
  if (data.slots.length >= 200) return notice('Limite da demonstração atingido. Reinicie para continuar.');
  data.slots.push({unit,date,time,done:false});
  data.log.push(`SIMULAÇÃO: vaga liberada em ${unit}, ${date} às ${time}.`);
  notice('Vaga fictícia liberada. Simule a convocação na lista de vagas.'); save(); render();
};
$('reset').onclick = () => { if (confirm('Reiniciar somente os dados fictícios deste navegador?')) { data = start(); notice('Demonstração reiniciada.'); save(); render(); } };
document.querySelectorAll('[data-tab]').forEach(button => button.onclick = () => {
  document.querySelectorAll('[data-tab]').forEach(tab => { tab.classList.toggle('on', tab === button); tab.setAttribute('aria-pressed', String(tab === button)); });
  ['mapa','fila','painel'].forEach(id => $(id).classList.toggle('hide', button.dataset.tab !== id));
  if (button.dataset.tab === 'mapa' && map) requestAnimationFrame(() => map.resize());
  render();
});
render();
const cache = new Map();
let cities = [], metadata = null, requestId = 0;
async function fetchJSON(path) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20000);
  try {
    const response = await fetch(path, {signal:controller.signal, cache:'no-cache'});
    if (!response.ok) throw new Error(`Arquivo oficial indisponível (HTTP ${response.status}). Tente novamente em alguns minutos.`);
    return await response.json();
  } finally { clearTimeout(timer); }
}
function suggestions() {
  $('cities').replaceChildren(...cities.filter(c => c.uf === $('uf').value).sort((a,b) => a.name.localeCompare(b.name,'pt-BR')).map(c => new Option(c.name,c.name)));
}
function clearResults() {
  markers.forEach(m => m.remove()); markers = [];
  $('units').replaceChildren(); $('count').textContent = '0';
  $('selectedunit').replaceChildren(new Option('UBS demonstrativa', 'UBS demonstrativa'));
}
function showUnits(units) {
  $('count').textContent = units.length;
  const fragment = document.createDocumentFragment();
  units.forEach(unit => {
    const title = `${unit.name} — CNES ${unit.cnes}`;
    $('selectedunit').add(new Option(title, title));
    const button = document.createElement('button'); button.className = 'unit'; button.dataset.cnes = unit.cnes;
    const located = Number.isFinite(unit.lat) && Number.isFinite(unit.lon) && unit.coordinate_status === 'validada_malha_ibge';
    const location = located ? 'Coordenada CNES validada no município' : unit.coordinate_status === 'fora_do_municipio' ? 'Somente na lista: coordenada fora da malha municipal' : 'Somente na lista: sem coordenadas válidas';
    button.innerHTML = `<strong>${escapeHtml(unit.name)}</strong><small>${escapeHtml([unit.address, unit.neighborhood].filter(Boolean).join(' • ') || 'Endereço não informado')}<br>CNES: ${escapeHtml(unit.cnes)} • ${escapeHtml(unit.city)}/${unit.uf}<br>${location}</small>`;
    let pin = null;
    if (located && map) {
      pin = new maplibregl.Marker({color:'#09866e'}).setLngLat([unit.lon,unit.lat]).setPopup(new maplibregl.Popup({offset:24}).setHTML(`<strong>${escapeHtml(unit.name)}</strong><p>${escapeHtml(unit.address)}<br>CNES: ${escapeHtml(unit.cnes)}</p><small>Fonte: CNES. Confirme o endereço com a unidade.</small>`)).addTo(map);
      markers.push(pin);
    }
    button.onclick = () => {
      $('selectedunit').value = title;
      document.querySelectorAll('.unit.selected').forEach(item => item.classList.remove('selected'));
      button.classList.add('selected');
      if (pin) { map.flyTo({center:[unit.lon,unit.lat],zoom:15}); if (!pin.getPopup().isOpen()) pin.togglePopup(); }
    };
    fragment.append(button);
  });
  $('units').append(fragment);
  if (map && markers.length) {
    const bounds = new maplibregl.LngLatBounds(); markers.forEach(pin => bounds.extend(pin.getLngLat()));
    map.fitBounds(bounds,{padding:40,maxZoom:14,duration:0});
  }
}
async function search() {
  const city = $('city').value.trim(), uf = $('uf').value;
  if (!city) { $('status').textContent = 'Digite ou selecione um município.'; return; }
  const thisRequest = ++requestId;
  $('search').disabled = true; clearResults(); $('status').textContent = 'Consultando dados oficiais…';
  try {
    if (!cities.length) { cities = await fetchJSON('./dados/municipios.json'); suggestions(); }
    const match = cities.find(c => c.uf === uf && normalizeName(c.name) === normalizeName(city));
    if (!match) { $('status').textContent = `Município não encontrado em ${uf}. Confira a UF e escolha uma sugestão.`; return; }
    if (!cache.has(uf)) cache.set(uf, await fetchJSON(`./dados/${uf}.json`));
    if (thisRequest !== requestId) return;
    const units = cache.get(uf).filter(unit => unit.city_id === match.id);
    $('city').value = match.name;
    showUnits(units);
    const mapped = units.filter(u => u.lat !== null && u.lon !== null).length;
    $('status').textContent = units.length ? `${units.length} unidades do conjunto oficial em ${match.name}/${uf}. ${mapped} com coordenadas validadas; ${units.length-mapped} somente na lista.` : `Nenhum registro deste município na versão importada. Isso não comprova ausência de UBS; consulte o CNES.`;
  } catch (error) {
    if (thisRequest === requestId) $('status').textContent = error.name === 'AbortError' ? 'A consulta demorou demais. Verifique sua conexão e tente novamente.' : error.message;
  } finally { if (thisRequest === requestId) $('search').disabled = false; }
}
$('uf').onchange = suggestions;
$('search').onclick = search;
$('city').onkeydown = event => { if (event.key === 'Enter' && !$('search').disabled) search(); };
fetchJSON('./dados/meta.json').then(meta => {
  metadata = meta;
  $('data-status').textContent = `Base importada em ${new Date(meta.updated_at).toLocaleString('pt-BR')}: ${meta.count.toLocaleString('pt-BR')} registros nacionais.`;
}).catch(() => { $('data-status').textContent = 'Data da atualização indisponível.'; });
search();
