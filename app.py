import streamlit as st
import pandas as pd
import urllib.parse
import re

# ID da Planilha e GIDs
DOC_ID = "1Dq9BXjt9tbsdFQryC3NBYJTXvhHjZbtEGdG_ZXpWdp0"

GIDS = {
    "LIVROS": "1591861167",
    "SÉRIES": "1513581778",
    "UNIVERSO MARVEL": "1360927897"
}

st.set_page_config(
    page_title="Procrastinação Organizada",
    page_icon="🍿",
    layout="wide"
)

# Estilização CSS do Layout Compacto
st.markdown("""
<style>
    .stApp { background-color: #14181c; color: #9ab; }
    h1, h2, h3, h4 { color: #ffffff !important; }
    .stProgress > div > div > div > div { background-color: #00e054; }
    
    div[data-testid="stImage"] img {
        border-radius: 6px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.5) !important;
        object-fit: cover !important;
        height: 120px !important;
        width: 80px !important;
    }
    .pdf-btn {
        display: inline-block;
        padding: 6px 12px;
        background-color: #ff4b4b;
        color: white !important;
        border-radius: 4px;
        text-decoration: none;
        font-size: 13px;
        font-weight: bold;
        margin-top: 6px;
        margin-bottom: 6px;
    }
    .pdf-btn:hover {
        background-color: #e03e3e;
    }
</style>
""", unsafe_allow_html=True)

def generate_fallback_card(text, bg="1e293b"):
    clean_title = re.sub(r'[^\w\s]', '', str(text)).strip()[:15]
    encoded = urllib.parse.quote(clean_title if clean_title else "Item")
    return f"https://dummyimage.com/150x225/{bg}/ffffff.png&text={encoded}"

# --- CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=60)
def load_data(sheet_name):
    try:
        gid = GIDS.get(sheet_name, "0")
        url = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/export?format=csv&gid={gid}"
        df = pd.read_csv(url, header=None)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar {sheet_name}: {e}")
        return pd.DataFrame()

# --- INTERFACE PRINCIPAL ---
st.title("🍿 Procrastinação Organizada")
st.caption("Seu Hub Pessoal de Entretenimento")

aba_livros, aba_series, aba_marvel = st.tabs(["📚 Biblioteca Virtual", "📺 Tracker de Séries", "🦸 Universo Marvel"])

# 1. BIBLIOTECA VIRTUAL (LIVROS)
with aba_livros:
    data_l = load_data("LIVROS")
    if not data_l.empty:
        df_l = data_l.iloc[3:].copy().dropna(how="all")
        
        # Mapeamento de colunas padrão da aba Livros
        # Coluna 1: Título | Coluna 2: Autor | Coluna 3: Gênero | Coluna 4: Status | Coluna 5 (Capa): Link do PDF
        df_l.columns = ["Index", "Título", "Autor", "Gênero", "Status", "Capa"] + list(df_l.columns[6:])
        df_l = df_l[df_l["Título"].fillna("").astype(str).str.strip() != ""]
        df_l = df_l[~df_l["Título"].astype(str).str.upper().isin(["TITULO", "TÍTULO"])]

        lidos = len(df_l[df_l["Status"].astype(str).str.upper().str.strip() == "LIDO"])
        tot_l = len(df_l)
        pct_l = int((lidos / tot_l) * 100) if tot_l > 0 else 0
        
        st.subheader(f"Biblioteca Virtual: {lidos}/{tot_l} lidos ({pct_l}%)")
        st.progress(lidos / tot_l if tot_l > 0 else 0)

        # Filtros e Pesquisa
        col_f1, col_f2 = st.columns([1, 2])
        with col_f1:
            generos = ["Todos"] + [str(g) for g in df_l["Gênero"].dropna().unique() if str(g).strip()]
            gen_selected = st.selectbox("Gênero:", generos, key="gen_l")
        with col_f2:
            search_l = st.text_input("🔍 Pesquisar livro...", key="search_l")

        if gen_selected != "Todos":
            df_l = df_l[df_l["Gênero"].astype(str) == gen_selected]
        if search_l:
            df_l = df_l[df_l["Título"].astype(str).str.contains(search_l, case=False, na=False)]

        # Paginação
        itens_por_pagina = 20
        total_paginas = (len(df_l) - 1) // itens_por_pagina + 1 if len(df_l) > 0 else 1
        
        col_p1, col_p2 = st.columns([1, 3])
        with col_p1:
            pagina = st.number_input("Página", min_value=1, max_value=total_paginas, value=1, step=1, key="pag_l")
        with col_p2:
            st.caption(f"Página {pagina} de {total_paginas} ({len(df_l)} livros encontrados)")

        inicio = (pagina - 1) * itens_por_pagina
        df_pagina = df_l.iloc[inicio:inicio + itens_por_pagina]

        st.divider()

        cols = st.columns(2)
        for idx, (_, row) in enumerate(df_pagina.iterrows()):
            with cols[idx % 2]:
                c1, c2 = st.columns([1, 4])
                
                # Trata link da Coluna Capa (PDF do Drive)
                capa_val = str(row.get("Capa", "")).strip()
                is_pdf_link = any(k in capa_val.lower() for k in ["drive.google.com", "docs.google.com", ".pdf", "http"])
                
                with c1:
                    # Exibe imagem promocional ou card estilizado
                    cover_img = generate_fallback_card(row["Título"], bg="0f172a")
                    st.image(cover_img)
                with c2:
                    st.write(f"**#{inicio + idx + 1} - {row['Título']}**")
                    st.caption(f"✍️ {row['Autor']} | 🏷️ {row['Gênero']}")
                    
                    # Botão Direto para o PDF do Google Drive
                    if is_pdf_link:
                        st.markdown(f'<a href="{capa_val}" target="_blank" class="pdf-btn">📄 Abrir PDF no Drive</a>', unsafe_allow_html=True)
                    else:
                        st.caption("📄 PDF não disponível")

                    is_lido = (str(row["Status"]).upper().strip() == "LIDO")
                    st.checkbox("Lido", value=is_lido, key=f"livro_{inicio + idx}")
                st.markdown("---")

# 2. TRACKER DE SÉRIES
with aba_series:
    data_s = load_data("SÉRIES")
    if not data_s.empty:
        df_s = data_s.iloc[3:, [0, 1, 2, 3]].copy()
        df_s.columns = ["Série", "Temporada", "Streaming", "Status"]
        df_s["Série"] = df_s["Série"].replace("", None).ffill()
        df_s = df_s[df_s["Série"].fillna("").astype(str).str.strip() != ""]
        df_s = df_s[~df_s["Série"].astype(str).str.upper().isin(["SÉRIIE", "SÉRIE", "SERIE"])]

        fin = len(df_s[df_s["Status"].astype(str).str.upper().str.strip() == "FINALIZADA"])
        tot_s = len(df_s)
        pct_s = int((fin / tot_s) * 100) if tot_s > 0 else 0
        
        st.subheader(f"Progresso de Séries: {fin}/{tot_s} Temporadas Finalizadas ({pct_s}%)")
        st.progress(fin / tot_s if tot_s > 0 else 0)
        
        search_s = st.text_input("🔍 Pesquisar série...", key="search_s")
        series_unicas = df_s.drop_duplicates(subset=["Série"])
        
        if search_s:
            series_unicas = series_unicas[series_unicas["Série"].astype(str).str.contains(search_s, case=False, na=False)]

        st.divider()

        cols_s = st.columns(2)
        for idx, (_, row) in enumerate(series_unicas.iterrows()):
            with cols_s[idx % 2]:
                c1, c2 = st.columns([1, 4])
                with c1:
                    poster_url = generate_fallback_card(row["Série"], bg="1e1b4b")
                    st.image(poster_url)
                with c2:
                    st.write(f"**#{idx+1} - {row['Série']}**")
                    st.caption(f"📺 {row['Temporada']} | 🍿 {row['Streaming']}")
                    is_finalizada = (str(row["Status"]).upper().strip() == "FINALIZADA")
                    st.checkbox("Finalizada", value=is_finalizada, key=f"serie_{idx}")
                st.markdown("---")

# 3. UNIVERSO MARVEL
with aba_marvel:
    data_m = load_data("UNIVERSO MARVEL")
    if not data_m.empty:
        df_m = data_m.iloc[4:, [0, 1, 2, 3]].copy()
        df_m.columns = ["Título", "Tipo", "Ano", "Status"]
        df_m = df_m[df_m["Título"].fillna("").astype(str).str.strip() != ""]
        df_m = df_m[~df_m["Título"].astype(str).str.upper().isin(["TITULO", "TÍTULO"])]

        ass = len(df_m[df_m["Status"].astype(str).str.upper().str.strip() == "SIM"])
        tot_m = len(df_m)
        pct_m = int((ass / tot_m) * 100) if tot_m > 0 else 0
        
        st.subheader(f"Maratona MCU: {ass}/{tot_m} assistidos ({pct_m}%)")
        st.progress(ass / tot_m if tot_m > 0 else 0)
        
        search_m = st.text_input("🔍 Pesquisar no Universo Marvel...", key="search_m")
        if search_m:
            df_m = df_m[df_m["Título"].astype(str).str.contains(search_m, case=False, na=False)]

        st.divider()

        cols_m = st.columns(2)
        for idx, (_, row) in enumerate(df_m.iterrows()):
            with cols_m[idx % 2]:
                c1, c2 = st.columns([1, 4])
                with c1:
                    poster_url = generate_fallback_card(row["Título"], bg="450a0a")
                    st.image(poster_url)
                with c2:
                    st.write(f"**#{idx+1} - {row['Título']}**")
                    st.caption(f"🎬 {row['Tipo']} | 📅 {row['Ano']}")
                    is_checked = (str(row["Status"]).upper().strip() == "SIM")
                    st.checkbox("Assistido", value=is_checked, key=f"mcu_{idx}")
                st.markdown("---")
