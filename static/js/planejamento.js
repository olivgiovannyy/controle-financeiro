/* Metas, planejamento e comparação: cada página usa apenas sua inicialização. */
const pagina = document.body.dataset.pagina;
async function iniciarMetas() {
  const form=document.querySelector('#form-meta');
  let metas=[];
  async function carregar() {
    metas=await api('/api/metas');
    document.querySelector('#metas').innerHTML=metas.map(m=>`<article class="meta"><div class="entre"><strong>${escapar(m.nome)}</strong><span>${porcentagem(m.percentual)}</span></div><progress value="${Math.min(m.percentual,100)}" max="100" aria-label="Progresso de ${escapar(m.nome)}"></progress><p>${moeda(m.guardado)} de ${moeda(m.valor)}</p><p>${m.faltam>0?`Faltam ${moeda(m.faltam)}.`:'Meta alcançada!'}</p><div class="acoes"><button class="secundario" data-editar="${escapar(m.id)}">Atualizar</button><button class="perigo" data-excluir="${escapar(m.id)}">Excluir</button></div></article>`).join('') || '<p class="vazio">Sua próxima conquista começa com uma meta.</p>';
  }
  form.addEventListener('reset',()=>{form.elements.id.value=''; document.querySelector('#meta-titulo').textContent='Nova meta';});
  form.addEventListener('submit',async e=>{
    e.preventDefault(); const botao=form.querySelector('button');botao.disabled=true;
    const dados=Object.fromEntries(new FormData(form));
    try { await api(dados.id?`/api/metas/${encodeURIComponent(dados.id)}`:'/api/metas',dados.id?'PUT':'POST',dados);form.reset();await carregar();aviso('Meta salva.'); }
    catch(erro){aviso(erro.message,true);}finally{botao.disabled=false;}
  });
  document.querySelector('#metas').addEventListener('click',async e=>{
    const b=e.target.closest('button');if(!b)return;
    if(b.dataset.editar){const m=metas.find(m=>m.id===b.dataset.editar);for(const campo of ['id','nome','valor','guardado'])form.elements[campo].value=m[campo];document.querySelector('#meta-titulo').textContent='Atualizar meta';form.elements.nome.focus();}
    if(b.dataset.excluir && confirm('Excluir esta meta?')){
      b.disabled=true;
      try{await api(`/api/metas/${encodeURIComponent(b.dataset.excluir)}`,'DELETE');await carregar();form.reset();aviso('Meta excluída.');}catch(erro){aviso(erro.message,true);b.disabled=false;}
    }
  });
  await carregar();
}
async function iniciarPlanejamento() {
  const mes=iniciarMes(), form=document.querySelector('#form-plano'), orcamento=document.querySelector('#form-orcamento');
  const categorias=await api('/api/categorias');
  document.querySelector('#categoria-orcamento').innerHTML=opcoesCategorias(categorias.despesa);
  let pedidoAtual=0;
  async function carregar() {
    if(!mes.value)return;
    const pedido=++pedidoAtual;
    sessionStorage.setItem('mes',mes.value);
    const d=await api('/api/dashboard?mes='+mes.value);
    if(pedido!==pedidoAtual)return;
    document.querySelector('#disponivel').textContent=moeda(d.plano.disponivel);
    document.querySelector('#saldo-nota').textContent=d.saldo<0?`Déficit de ${moeda(-d.saldo)}. Nenhum valor disponível para distribuir.`:'Disponíveis após as despesas do mês selecionado.';
    document.querySelector('#percentuais').innerHTML=Object.entries(d.plano.percentuais).map(([c,p])=>`<label>${escapar(c)} (%)<input type="number" name="${escapar(c)}" min="0" max="100" step="1" value="${p}" required></label>`).join('');
    grafico('plano','doughnut',Object.keys(d.plano.valores),[{data:Object.values(d.plano.valores)}]);
    document.querySelector('#plano-texto').innerHTML=Object.entries(d.plano.valores).map(([c,v])=>`<div class="entre"><span>${escapar(c)}</span><strong>${moeda(v)}</strong></div>`).join('');
    renderOrcamentos(d.orcamentos,true);
  }
  mes.addEventListener('change',()=>carregar().catch(e=>aviso(e.message,true)));
  form.addEventListener('submit',async e=>{
    e.preventDefault();const b=form.querySelector('button');b.disabled=true;
    const percentuais=Object.fromEntries([...new FormData(form)].map(([c,p])=>[c,Number(p)]));
    try{await api('/api/planejamento','PUT',{mes:mes.value,percentuais});await carregar();aviso('Divisão salva para este mês.');}catch(erro){aviso(erro.message,true);}finally{b.disabled=false;}
  });
  orcamento.addEventListener('submit',async e=>{
    e.preventDefault();const b=orcamento.querySelector('button');b.disabled=true;
    try{await api('/api/orcamentos','PUT',{...Object.fromEntries(new FormData(orcamento)),mes:mes.value});await carregar();aviso('Limite salvo.');}catch(erro){aviso(erro.message,true);}finally{b.disabled=false;}
  });
  document.querySelector('#orcamentos').addEventListener('click',async e=>{
    const b=e.target.closest('[data-remover]');if(!b || !confirm('Remover este limite mensal?'))return;
    b.disabled=true;
    try{await api('/api/orcamentos','DELETE',{mes:mes.value,categoria:b.dataset.remover});await carregar();aviso('Limite removido.');}catch(erro){aviso(erro.message,true);b.disabled=false;}
  });
  await carregar();
}
async function iniciarRelatorios() {
  const form=document.querySelector('#form-comparacao');
  const hoje=new Date(), anterior=new Date(hoje.getFullYear(),hoje.getMonth()-1,1);
  form.elements.primeiro.value=`${anterior.getFullYear()}-${String(anterior.getMonth()+1).padStart(2,'0')}`;
  form.elements.segundo.value=mesAtual();
  async function carregar(){
    const params=new URLSearchParams(new FormData(form));
    const d=await api('/api/comparacao?'+params);
    const mesBR=v=>v.split('-').reverse().join('/');
    document.querySelector('#comparacao').innerHTML=`<div class="tabela"><table><thead><tr><th>Indicador</th><th>${mesBR(form.elements.primeiro.value)}</th><th>${mesBR(form.elements.segundo.value)}</th></tr></thead><tbody>${[['receitas','Receitas'],['despesas','Despesas'],['saldo','Saldo'],['economia','Economia disponível']].map(([k,n])=>`<tr><td>${n}</td><td>${moeda(d.primeiro[k])}</td><td>${moeda(d.segundo[k])}</td></tr>`).join('')}</tbody></table></div><ul class="insights"><li>${d.variacao_despesas===null?'O primeiro mês não possui despesas; não há base para calcular a variação percentual.':`Variação de despesas do primeiro para o segundo mês: ${porcentagem(d.variacao_despesas)}.`}</li><li>${d.maior_aumento?`Maior aumento: ${escapar(d.maior_aumento.categoria)}, ${moeda(d.maior_aumento.variacao)}.`:'Nenhuma categoria aumentou.'}</li><li>${d.maior_reducao?`Maior redução: ${escapar(d.maior_reducao.categoria)}, ${moeda(-d.maior_reducao.variacao)}.`:'Nenhuma categoria diminuiu.'}</li></ul>`;
  }
  form.addEventListener('submit',async e=>{e.preventDefault();const b=form.querySelector('button');b.disabled=true;try{await carregar();}catch(erro){aviso(erro.message,true);}finally{b.disabled=false;}});
  await carregar();
}
(async()=>{
  try {
    if(pagina==='metas') await iniciarMetas();
    if(pagina==='planejamento') await iniciarPlanejamento();
    if(pagina==='relatorios') await iniciarRelatorios();
  } catch(erro) { aviso(erro.message,true); }
})();
