# 🎯 Sales Automation Suite (Hunter & Sniper)

Uma suite completa de ferramentas de prospecção B2B desenvolvida em Python.

## 🛠️ Ferramentas Inclusas

### 1. 🕵️ G-Maps Hunter (v3.4)
Minerador de dados geoespaciais.
- **Função:** Extrai leads qualificados diretamente do Google Maps.
- **Filtros:** Possui "Firewall Geográfico" para limpar resultados imprecisos (ex: remover SP de buscas no RJ).
- **Stack:** Playwright + Streamlit.

### 2. 🔫 Sales Sniper (v2.3)
Agente de Enriquecimento com IA.
- **Função:** Cria scripts de abordagem (Cold Messaging) personalizados.
- **IA:** Integrado com Google Gemini 1.5 Flash (Custo Zero).
- **Segurança:** Sistema anti-bloqueio (Rate Limit Retry) automático.

## 🚀 Como Rodar

1. Clone o repositório.
2. Instale as dependências:
   pip install -r requirements.txt
   playwright install