import asyncio
import sys

# --- CORREÇÃO PARA WINDOWS ---
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
from playwright.sync_api import sync_playwright
import pandas as pd
import time
import random

# --- CONFIGURAÇÃO DA INTERFACE ---
st.set_page_config(page_title="G-Maps Hunter v3.4 (Final)", page_icon="🎯", layout="wide")

st.title("🎯 G-Maps Hunter v3.4 (Versão Final)")
st.markdown("**Status:** Operacional | Filtro de Texto Livre | Persistência Ativa")

# --- INICIALIZAÇÃO DA MEMÓRIA ---
if 'dados_extraidos' not in st.session_state:
    st.session_state['dados_extraidos'] = None

with st.sidebar:
    st.header("⚙️ Configurações")
    termo_busca = st.text_input("Alvo:", placeholder="Ex: Pizzaria em Centro, BH")
    
    # --- FILTRO DE PRECISÃO (TEXTO LIVRE) ---
    st.divider()
    st.markdown("🕵️ **Filtro de Qualidade**")
    filtro_local = st.text_input("Deve conter no endereço:", placeholder="Ex: RJ (ou nome da rua)", help="Deixe vazio para trazer tudo. O robô descartará qualquer lead que não tenha esse texto no endereço.")
    
    qtd_scrolls = st.slider("Profundidade (Scrolls)", 1, 20, 5)
    
    def limpar_memoria():
        st.session_state['dados_extraidos'] = None
        
    botao_iniciar = st.button("🚀 Iniciar Mineração", type="primary", on_click=limpar_memoria)

# --- MOTOR DE EXTRAÇÃO ---
def extrair_detalhes(page):
    """Extrai telefone, site, nota e ENDEREÇO."""
    dados = {"Telefone": "N/A", "Site": "N/A", "Nota": "N/A", "Endereco": "N/A"}
    try:
        # 1. Telefone
        try:
            btn_phone = page.locator("button[data-item-id^='phone:']").first
            if btn_phone.count() > 0:
                raw = btn_phone.get_attribute("aria-label")
                if raw:
                    dados["Telefone"] = raw.replace("Ligar para: ", "").replace("Ligar para ", "").strip()
        except: pass

        # 2. Site
        try:
            btn_site = page.locator("a[data-item-id='authority']").first
            if btn_site.count() > 0:
                dados["Site"] = btn_site.get_attribute("href")
        except: pass

        # 3. Nota
        try:
            nota_el = page.locator("div[role='img'][aria-label*='estrelas']").first
            if nota_el.count() > 0:
                dados["Nota"] = nota_el.get_attribute("aria-label").split(" ")[0]
            else:
                span_nota = page.locator("span.fontBodyMedium > span").first
                if span_nota.count() > 0:
                    dados["Nota"] = span_nota.inner_text()
        except: pass

        # 4. Endereço (Essencial para o filtro)
        try:
            btn_end = page.locator("button[data-item-id='address']").first
            if btn_end.count() > 0:
                raw_end = btn_end.get_attribute("aria-label")
                if raw_end:
                    dados["Endereco"] = raw_end.replace("Endereço: ", "").strip()
        except: pass

    except: pass
    return dados

def rodar_robo(termo, scrolls, filtro_obrigatorio):
    status_main = st.status(f"🔧 Inicializando Robô... (Filtro: {filtro_obrigatorio if filtro_obrigatorio else 'Nenhum'})", expanded=True)
    lista_final = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--start-maximized", "--no-sandbox"]
        )
        context = browser.new_context(locale="pt-BR")
        page = context.new_page()

        status_main.write(f"🌍 Acessando Google Maps...")
        page.goto("https://www.google.com.br/maps?hl=pt-BR", timeout=60000)
        
        try:
            status_main.write(f"🔍 Buscando por: {termo}")
            page.wait_for_selector("input#searchboxinput", timeout=15000)
            page.fill("input#searchboxinput", termo)
            page.keyboard.press("Enter")
        except:
            status_main.error("❌ Erro: Caixa de busca não encontrada.")
            browser.close()
            return pd.DataFrame()

        status_main.write("⏳ Aguardando resultados...")
        try:
            page.wait_for_selector("div[role='feed']", timeout=15000)
        except:
            status_main.warning("⚠️ Demora no carregamento...")

        for i in range(scrolls):
            page.hover("div[role='feed']")
            page.mouse.wheel(0, 3000)
            time.sleep(3)
            status_main.write(f"   📜 Scroll {i+1}/{scrolls}...")

        status_main.write("👀 Listando candidatos...")
        elementos = page.locator("div[role='feed'] a[href*='/maps/place']").all()
        
        links_unicos = set()
        lista_preliminar = []
        for el in elementos:
            link = el.get_attribute("href")
            nome = el.get_attribute("aria-label")
            if link and nome and link not in links_unicos:
                links_unicos.add(link)
                lista_preliminar.append({"Empresa": nome, "Link": link})
        
        total_leads = len(lista_preliminar)
        status_main.write(f"✅ Fase 1: {total_leads} locais encontrados. Iniciando filtragem...")

        if total_leads > 0:
            progress_bar = status_main.progress(0)
            leads_validos = 0
            
            for i, item in enumerate(lista_preliminar):
                try:
                    page.goto(item["Link"], timeout=30000)
                    page.wait_for_selector("h1", timeout=5000)
                    detalhes = extrair_detalhes(page)
                    
                    # --- LÓGICA DO FIREWALL ---
                    passou_no_filtro = True
                    motivo_filtro = ""
                    
                    if filtro_obrigatorio:
                        # Verifica se o texto do filtro está contido no endereço (case insensitive)
                        if filtro_obrigatorio.lower() not in detalhes["Endereco"].lower():
                            passou_no_filtro = False
                            motivo_filtro = "(Filtro de Localização)"
                    
                    if passou_no_filtro:
                        item_completo = {
                            "Empresa": item["Empresa"],
                            "Telefone": detalhes["Telefone"],
                            "Site": detalhes["Site"],
                            "Nota": detalhes["Nota"],
                            "Endereco": detalhes["Endereco"],
                            "Link Maps": item["Link"]
                        }
                        lista_final.append(item_completo)
                        leads_validos += 1
                        
                        tel_display = detalhes['Telefone'] if detalhes['Telefone'] != "N/A" else "---"
                        status_main.write(f"   ✅ {item['Empresa'][:20]}... | 📞 {tel_display}")
                    else:
                        status_main.write(f"   🗑️ {item['Empresa'][:20]}... removido {motivo_filtro}")

                except: pass
                progress_bar.progress((i + 1) / total_leads)
        
        browser.close()
        status_main.update(label=f"🎉 Finalizado! {leads_validos} leads qualificados.", state="complete", expanded=False)

    return pd.DataFrame(lista_final)

# --- FLUXO DE CONTROLE ---
if botao_iniciar and termo_busca:
    st.session_state['dados_extraidos'] = rodar_robo(termo_busca, qtd_scrolls, filtro_local)

if st.session_state['dados_extraidos'] is not None:
    df = st.session_state['dados_extraidos']
    if not df.empty:
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("Leads Filtrados", len(df))
        c2.metric("Com Telefone", len(df[df["Telefone"] != "N/A"]))
        
        st.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False, sep=';', encoding='utf-8-sig')
        st.download_button(
            label="📥 Baixar Dados Limpos (CSV)",
            data=csv,
            file_name=f"leads_gmaps_{termo_busca.replace(' ', '_')}.csv",
            mime="text/csv",
        )
    else:
        st.warning(f"Nenhum lead passou pelo filtro '{filtro_local}'. Tente deixar o filtro vazio.")