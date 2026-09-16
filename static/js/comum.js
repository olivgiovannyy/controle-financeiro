/* Funções compartilhadas. Regras e totais financeiros vêm sempre do Python. */
const moeda = valor => new Intl.NumberFormat('pt-BR', {style:'currency', currency:'BRL'}).format(valor);
const porcentagem = valor => valor === null ? 'Não se aplica' : `${new Intl.NumberFormat('pt-BR', {maximumFractionDigits:1}).format(valor)}%`;
const dataBR = data => data.split('-').reverse().join('/');
const mesAtual = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`; };
// Conteúdo digitado nunca vira HTML executável ao montar a interface.
const escapar = valor => String(valor).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const graficos = {};
function aviso(texto, erro=false) {
  const elemento = document.querySelector('#mensagem');
  elemento.textContent = texto; elemento.hidden = false;
  elemento.className = erro ? 'erro' : '';
}
// async/await espera a resposta sem bloquear a página. fetch chama a API Flask.
async function api(url, metodo='GET', dados) {
  const opcoes = {method:metodo, headers:{}};
  if (dados !== undefined) {
    opcoes.headers['Content-Type'] = 'application/json';
    opcoes.body = JSON.stringify(dados);
  }
  let resposta;
  try { resposta = await fetch(url, opcoes); }
  catch { throw new Error('Não foi possível conectar ao Python. Confira se o servidor está ligado.'); }
  const json = await resposta.json();
  if (!resposta.ok) throw new Error(json.erro || 'Não foi possível concluir a operação.');
  return json;
}
function iniciarMes() {
  const campo = document.querySelector('#mes');
  campo.value = sessionStorage.getItem('mes') || mesAtual();
  return campo;
}
function opcoesCategorias(categorias) {
  return categorias.map(c => `<option value="${escapar(c)}">${escapar(c)}</option>`).join('');
}
function grafico(id, tipo, etiquetas, series) {
  if (!window.Chart) {
    aviso('Os gráficos precisam de conexão à internet para carregar o Chart.js. Os demais recursos continuam disponíveis.', true);
    return;
  }
  if (graficos[id]) graficos[id].destroy();
  const cores = ['#168364','#9bd5b7','#dfa456','#578aa4','#b7bbde','#b65762','#748b80','#bbcbad','#9f7351','#6477a6'];
  const circular = tipo === 'doughnut';
  // Chart.js desenha os valores que o backend já calculou.
  graficos[id] = new Chart(document.getElementById(id), {
    type:tipo,
    data:{labels:etiquetas, datasets:series.map((s,i) => ({...s,
      backgroundColor:s.backgroundColor || (circular ? cores : cores[i]),
      borderColor:s.borderColor || cores[i], borderWidth:tipo === 'line' ? 2.5 : 0,
      borderRadius:tipo === 'bar' ? 5 : 0, tension:.3, pointRadius:3}))},
    options:{responsive:true, maintainAspectRatio:false,
      ...(circular ? {cutout:'72%'} : {scales:{y:{beginAtZero:true,ticks:{callback:v=>moeda(v)},grid:{color:'#edf1ef'}},x:{grid:{display:false}}}}),
      plugins:{legend:{position:'bottom',labels:{usePointStyle:true,boxWidth:8,padding:18,font:{size:12}}},
      tooltip:{callbacks:{label:c=>`${c.dataset.label || c.label}: ${moeda(circular ? c.parsed : c.parsed.y)}`}}}}
  });
}
function renderOrcamentos(itens, editar=false) {
  const elemento = document.querySelector('#orcamentos');
  elemento.innerHTML = itens.length ? itens.map(o => `<div class="orcamento ${o.percentual>=100?'estourado':o.percentual>=80?'atencao':''}">
    <div class="entre"><strong>${escapar(o.categoria)}</strong><span>${porcentagem(o.percentual)}</span></div>
    <progress max="100" value="${Math.min(o.percentual,100)}" aria-label="Limite de ${escapar(o.categoria)}"></progress>
    <p>${moeda(o.gasto)} de ${moeda(o.limite)}</p>
    ${o.excesso>0?`<small class="negativo">Limite ultrapassado em ${moeda(o.excesso)}.</small>`:''}
    ${editar?`<button class="secundario" data-remover="${escapar(o.categoria)}">Remover limite</button>`:''}</div>`).join('') : '<p class="vazio">Nenhum limite definido para este mês.</p>';
}
