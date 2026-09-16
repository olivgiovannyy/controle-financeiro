const modal = document.querySelector('#modal');
const formulario = document.querySelector('#form-transacao');
const filtros = document.querySelector('#filtros');
let categorias, registros = [], pedidoAtual = 0;
function preencherCategorias() {
  formulario.elements.categoria.innerHTML = opcoesCategorias(categorias[formulario.elements.tipo.value]);
}
async function carregarTransacoes() {
  const pedido = ++pedidoAtual;
  const params = new URLSearchParams();
  for (const [chave, valor] of new FormData(filtros)) if (valor) params.set(chave,valor);
  try {
    const dados = await api('/api/transacoes?'+params);
    if (pedido !== pedidoAtual) return;
    registros = dados;
    document.querySelector('#linhas').innerHTML = registros.length ? registros.map(t=>`<tr><td>${dataBR(t.data)}</td><td>${escapar(t.descricao)}</td><td>${escapar(t.categoria)}</td><td><span class="badge ${t.tipo}">${t.tipo==='receita'?'Receita':'Despesa'}</span></td><td class="${t.tipo==='receita'?'positivo':'negativo'}">${moeda(t.valor)}</td><td><button class="secundario" data-editar="${escapar(t.id)}">Editar</button><button class="perigo" data-excluir="${escapar(t.id)}">Excluir</button></td></tr>`).join('') : '<tr><td colspan="6" class="vazio">Nenhuma transação encontrada. Que tal registrar a primeira?</td></tr>';
    document.querySelector('#contagem').textContent = `${registros.length} transação(ões) encontrada(s)`;
  } catch(erro) { aviso(erro.message,true); }
}
function abrir(item) {
  formulario.reset();
  formulario.elements.id.value='';
  formulario.elements.tipo.value=item?.tipo || 'despesa';
  preencherCategorias();
  if (item) for (const campo of ['id','descricao','valor','data','categoria']) formulario.elements[campo].value=item[campo];
  else { const d=new Date(); formulario.elements.data.value=`${mesAtual()}-${String(d.getDate()).padStart(2,'0')}`; }
  document.querySelector('#erro-form').textContent='';
  document.querySelector('#titulo-modal').textContent=item?'Editar transação':'Nova transação';
  modal.showModal();
}
formulario.elements.tipo.addEventListener('change',preencherCategorias);
document.querySelector('#nova').addEventListener('click',()=>abrir());
document.querySelector('#fechar').addEventListener('click',()=>modal.close());
formulario.addEventListener('submit',async evento=>{
  evento.preventDefault();
  const botao=formulario.querySelector('[type=submit]'); botao.disabled=true;
  const dados=Object.fromEntries(new FormData(formulario));
  try {
    await api(dados.id?`/api/transacoes/${encodeURIComponent(dados.id)}`:'/api/transacoes',dados.id?'PUT':'POST',dados);
    modal.close(); aviso('Transação salva.'); await carregarTransacoes();
  } catch(erro) { document.querySelector('#erro-form').textContent=erro.message; }
  finally { botao.disabled=false; }
});
document.querySelector('#linhas').addEventListener('click',async evento=>{
  const botao=evento.target.closest('button'); if(!botao)return;
  if(botao.dataset.editar) abrir(registros.find(t=>t.id===botao.dataset.editar));
  if(botao.dataset.excluir && confirm('Excluir esta transação? Essa ação não pode ser desfeita.')) {
    botao.disabled=true;
    try { await api(`/api/transacoes/${encodeURIComponent(botao.dataset.excluir)}`,'DELETE'); aviso('Transação excluída.'); await carregarTransacoes(); }
    catch(erro) { aviso(erro.message,true); botao.disabled=false; }
  }
});
filtros.addEventListener('submit',evento=>{evento.preventDefault();carregarTransacoes();});
filtros.addEventListener('reset',()=>setTimeout(carregarTransacoes,0));
(async()=>{
  document.querySelector('#nova').disabled=true;
  try {
    categorias=await api('/api/categorias');
    document.querySelector('#filtro-categoria').innerHTML += opcoesCategorias([...new Set([...categorias.receita,...categorias.despesa])]);
    document.querySelector('#nova').disabled=false;
    await carregarTransacoes();
  } catch(erro) { aviso(erro.message,true); }
})();
