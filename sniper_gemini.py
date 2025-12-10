import streamlit as st
import pandas as pd
import google.generativeai as genai
import time
import random

# --- CONFIGURAÇÃO DA INTERFACE ---
st.set_page_config(page_title="Sales Sniper v2.3 (Fix)", page_icon="💎", layout="centered")

st.title("💎 Sales Sniper v2.3 (Final)")
st.markdown("Enriquecimento com IA + Retry Automático.")

# --- INPUTS ---
col_key, col_file = st.columns(2)

with col_key:
    # Limpeza de espaços invisíveis na chave
    raw_key = st.text_input("Google API Key:", type="password", help="Começa com AIza...")
    api_key = raw_key.strip() if raw_key else None

with col_file:
    uploaded_file = st.file_uploader("Suba o CSV do Hunter:", type=["csv"])

# --- SELEÇÃO DE MODELO ---
modelo_escolhido = None
if api_key:
    try:
        genai.configure(api_key=api_key)
        # Lista apenas modelos que geram texto
        modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Tenta selecionar o Flash automaticamente
        index_flash = 0
        for i, m in enumerate(modelos):
            if "flash" in m: index_flash = i; break
            
        st.divider()
        nome_modelo = st.selectbox("Cérebro da IA:", modelos, index=index_flash)
        modelo_escolhido = genai.GenerativeModel(nome_modelo)
    except Exception as e:
        st.error(f"Erro de Conexão com Google: {e}")

# --- LÓGICA DE GERAÇÃO (COM RETRY AUTOMÁTICO) ---
def gerar_com_retry(row, model):
    empresa = str(row.get('Empresa', 'Empresa'))
    nota = str(row.get('Nota', 'N/A'))
    site = str(row.get('Site', 'N/A'))
    endereco = str(row.get('Endereco', 'N/A'))
    
    prompt = f"""
    Atue como SDR B2B. Escreva uma mensagem fria de WhatsApp.
    SAÍDA: APENAS O TEXTO DA MENSAGEM.

    DADOS:
    Endereço: {endereco}
    Nota: {nota}
    Site: {site if "http" in site else "SEM SITE"}

    LÓGICA:
    - Sem Site: "Olá, tudo bem? Vi vocês no Maps em {endereco} mas sem site. Isso dificulta novos clientes. Faz sentido resolvermos?"
    - Nota Baixa (<4.0): "Olá, tudo bem? Notei que a nota {nota} no Google pode estar afastando clientes. Temos uma estratégia para subir isso. Quer conhecer?"
    - Nota Alta (>4.5): "Olá, tudo bem? Parabéns pela nota {nota}! Com essa reputação, já pensaram em automatizar o atendimento?"
    - Padrão: "Olá, tudo bem? Vi vocês no Maps da região. Estamos ajudando empresas locais a venderem mais pelo Google. Posso mandar uma ideia?"

    REGRAS: Máximo 3 frases. Tom casual. Termine com pergunta.
    """

    tentativas = 0
    max_tentativas = 5
    
    while tentativas < max_tentativas:
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        
        except Exception as e:
            erro_str = str(e)
            if "429" in erro_str:
                # Espera progressiva (15s, 25s, 35s...)
                tempo_espera = 15 + (tentativas * 10)
                # --- CORREÇÃO AQUI: Emoji direto ---
                st.toast(f"⏳ Limite atingido para {empresa}. Esperando {tempo_espera}s...", icon="☕")
                time.sleep(tempo_espera)
                tentativas += 1
            else:
                return f"Erro: {e}"
    
    return "ERRO: Falha após várias tentativas."

# --- PROCESSAMENTO ---
if uploaded_file and modelo_escolhido and st.button("⚡ Disparar Sniper", type="primary"):
    # Lê CSV com separador ponto e vírgula
    df = pd.read_csv(uploaded_file, sep=";")
    
    progress_bar = st.progress(0)
    status_box = st.status("Processando...", expanded=True)
    scripts = []
    
    total = len(df)
    start_time = time.time()
    
    for i, row in df.iterrows():
        nome = row.get('Empresa', 'Lead')
        status_box.write(f"🎯 Mirando: {nome}...")
        
        script = gerar_com_retry(row, modelo_escolhido)
        scripts.append(script)
        
        # Pausa padrão de segurança entre requisições
        time.sleep(5) 
        
        progress_bar.progress((i + 1) / total)
    
    df['Script_IA'] = scripts
    
    tempo_total = time.time() - start_time
    status_box.update(label=f"✅ Concluído em {tempo_total:.1f}s!", state="complete", expanded=False)
    
    st.dataframe(df[['Empresa', 'Script_IA']], use_container_width=True)
    
    st.download_button(
        "📥 Baixar Planilha Final",
        df.to_csv(index=False, sep=';', encoding='utf-8-sig'),
        "leads_sniper_v2_3.csv",
        "text/csv"
    )