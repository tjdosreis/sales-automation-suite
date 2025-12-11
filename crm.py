import streamlit as st
import pandas as pd
import urllib.parse
import os

# --- CONFIGURAÇÃO DA INTERFACE ---
st.set_page_config(page_title="War Room CRM v2.3", page_icon="⚔️", layout="wide")

st.title("⚔️ War Room CRM v2.3")
st.markdown("Gestão Visual de Leads e Disparo Rápido.")

# --- FUNÇÕES UTILITÁRIAS ---
def limpar_telefone(tel):
    """Remove caracteres não numéricos."""
    if pd.isna(tel) or str(tel).lower() in ['nan', 'n/a', 'none', '']: return None
    clean = ''.join(filter(str.isdigit, str(tel)))
    return clean

def formatar_display_telefone(val):
    """Formata o valor para exibição amigável na UI."""
    s = str(val).strip()
    if s.lower() in ['nan', 'n/a', 'none', '', '0', '0.0']:
        return "Sem número de telefone", False
    return s, True

def salvar_progresso():
    """Salva o DataFrame da memória para o arquivo local."""
    if 'df_crm' in st.session_state:
        caminho = st.session_state['db_path']
        st.session_state['df_crm'].to_csv(caminho, index=False, sep=';', encoding='utf-8-sig')
        st.toast("💾 Dados Salvos no Disco!", icon="✅")

# --- BARRA LATERAL (CARREGAMENTO INTELIGENTE) ---
with st.sidebar:
    st.header("📂 Carregar Missão")
    uploaded_file = st.file_uploader("Suba o CSV do Sniper:", type=["csv"])
    
    st.divider()
    filtro_status = st.radio(
        "Filtrar por Status:", 
        ["Todos", "Pendente", "Contatado", "Negociação", "Venda", "Descartado"]
    )
    
    if st.button("⚠️ Forçar Reinício (Apaga Progresso)"):
        if 'db_path' in st.session_state and os.path.exists(st.session_state['db_path']):
            os.remove(st.session_state['db_path'])
            st.session_state.clear()
            st.rerun()

    # LÓGICA DE CARREGAMENTO
    if uploaded_file:
        db_filename = f"crm_database_{uploaded_file.name}"
        
        if 'df_crm' not in st.session_state or st.session_state.get('arquivo_origem') != uploaded_file.name:
            if os.path.exists(db_filename):
                df = pd.read_csv(db_filename, sep=";")
                st.toast("📂 Histórico carregado!", icon="📂")
            else:
                df = pd.read_csv(uploaded_file, sep=";")
                if 'Status' not in df.columns: df['Status'] = 'Pendente'
                if 'Observacoes' not in df.columns: df['Observacoes'] = ''
                st.toast("✨ Nova missão iniciada!", icon="🚀")

            st.session_state['df_crm'] = df
            st.session_state['arquivo_origem'] = uploaded_file.name
            st.session_state['db_path'] = db_filename
            df.to_csv(db_filename, index=False, sep=';', encoding='utf-8-sig')

# --- DASHBOARD ---
if 'df_crm' in st.session_state:
    df = st.session_state['df_crm']
    
    # Aplica Filtro Visual
    if filtro_status != "Todos":
        df_view = df[df['Status'] == filtro_status]
    else:
        df_view = df

    # --- MÉTRICAS ---
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total", len(df))
    c2.metric("Pendentes", len(df[df['Status']=='Pendente']))
    c3.metric("Contatados", len(df[df['Status']=='Contatado']))
    c4.metric("Negociação", len(df[df['Status']=='Negociação']))
    c5.metric("Vendas", len(df[df['Status']=='Venda']))
    c6.metric("Descartados", len(df[df['Status']=='Descartado']))

    # --- BARRA DE STATUS VISUAL ---
    color_map = {
        "Todos": "#9b59b6",      # Roxo
        "Pendente": "#e67e22",   # Laranja
        "Contatado": "#3498db",  # Azul
        "Negociação": "#f1c40f", # Amarelo
        "Venda": "#2ecc71",      # Verde
        "Descartado": "#e74c3c"  # Vermelho
    }
    cor_atual = color_map.get(filtro_status, "#ccc")
    
    st.markdown(f"""
    <div style="text-align: center; border-bottom: 5px solid {cor_atual}; padding-bottom: 10px; margin-bottom: 20px;">
        <h4 style="color: {cor_atual}; margin:0;">📂 MODO: {filtro_status.upper()}</h4>
    </div>
    """, unsafe_allow_html=True)

    # --- VISUALIZAÇÃO DO LEAD ---
    if len(df_view) > 0:
        if 'idx_lead' not in st.session_state: st.session_state.idx_lead = 0
        if st.session_state.idx_lead >= len(df_view): st.session_state.idx_lead = 0
        
        lead = df_view.iloc[st.session_state.idx_lead]
        idx_real = df_view.index[st.session_state.idx_lead]

        col_dados, col_acoes = st.columns([1, 1])

        with col_dados:
            st.subheader(f"🏢 {lead.get('Empresa', 'Sem Nome')}")
            
            # --- TRATAMENTO VISUAL DO TELEFONE ---
            raw_tel = lead.get('Telefone', '')
            tel_display, tem_numero = formatar_display_telefone(raw_tel)
            
            if tem_numero:
                st.write(f"📞 **Telefone:** `{tel_display}`")
            else:
                st.caption(f"📞 {tel_display}") # Mostra cinza se não tiver número
            
            st.caption(f"📍 {lead.get('Endereco', '')}")
            st.write(f"**Status Atual:** `{lead['Status']}`")
            
            url_site = lead.get('Site', '')
            if isinstance(url_site, str) and "http" in url_site:
                st.link_button("🌐 Abrir Site", url_site)
            
            st.markdown("### 📝 Notas")
            obs = st.text_area("Diário de Bordo:", value=lead.get('Observacoes', ''), key=f"obs_{idx_real}")
            if st.button("Salvar Nota", key=f"save_{idx_real}"):
                df.at[idx_real, 'Observacoes'] = obs
                salvar_progresso()

        with col_acoes:
            st.subheader("💬 Script & Disparo")
            script = st.text_area("Mensagem:", value=lead.get('Script_IA', ''), height=150)
            
            # Lógica do Botão
            tel_clean = limpar_telefone(raw_tel)
            
            if tel_clean and len(tel_clean) >= 10:
                msg_safe = urllib.parse.quote(script)
                link_wa = f"https://web.whatsapp.com/send?phone=55{tel_clean}&text={msg_safe}"
                st.link_button("🚀 Enviar WhatsApp", link_wa, type="primary")
            else:
                # Feedback de Erro Polido
                if not tem_numero:
                    st.warning("⚠️ Sem número de telefone disponível.")
                else:
                    st.error(f"⚠️ Telefone inválido para link: {tel_display}")
            
            st.markdown("---")
            st.write("**Definir Novo Status:**")
            
            b1, b2, b3, b4 = st.columns(4)
            
            if b1.button("✅ Feito"):
                df.at[idx_real, 'Status'] = 'Contatado'
                salvar_progresso()
                st.rerun()
                
            if b2.button("💬 Resp."):
                df.at[idx_real, 'Status'] = 'Negociação'
                salvar_progresso()
                st.rerun()

            if b3.button("🤑 Venda"):
                df.at[idx_real, 'Status'] = 'Venda'
                salvar_progresso()
                st.rerun()
                
            if b4.button("❌ Lixo"):
                df.at[idx_real, 'Status'] = 'Descartado'
                salvar_progresso()
                st.rerun()

        st.divider()
        nc1, nc2, nc3 = st.columns([1, 4, 1])
        with nc1:
            if st.button("⬅️ Anterior") and st.session_state.idx_lead > 0:
                st.session_state.idx_lead -= 1
                st.rerun()
        with nc3:
            if st.button("Próximo ➡️") and st.session_state.idx_lead < len(df_view) - 1:
                st.session_state.idx_lead += 1
                st.rerun()
                
    else:
        st.info(f"Nenhum lead com status: {filtro_status}")
else:
    st.info("👈 Suba o CSV para iniciar a operação.")