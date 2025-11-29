import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import pandas as pd
import os
import ast

# def login():
#     st.title("🔒 Login")
#     usuario = st.text_input("Usuário")
#     senha = st.text_input("Senha", type="password")
#     if st.button("Entrar"):
#         # Usuário e senha fixos (exemplo)
#         if usuario == "admin" and senha == "1234":
#             st.session_state["autenticado"] = True
#         else:
#             st.error("Usuário ou senha incorretos.")

# if "autenticado" not in st.session_state or not st.session_state["autenticado"]:
#     login()
#     st.stop()

# Caminho
@st.cache_data
def carregar_dados():
    all_dfs = []
    path = "csvs"

    with open('dicionarios_partidos.txt',"r",encoding="utf-8") as f:
        meu_dict = ast.literal_eval(f.read())

    with open('lista_regionais.txt', "r", encoding="utf-8") as f:
        regionais_dict = ast.literal_eval(f.read())

    # dicionário: BAIRRO(UCASE)->REGIONAL
    bairro_para_regional = {
        (bairro or "").upper().strip(): regional for regional, bairros in regionais_dict.items() for bairro in bairros
    }

    for arquivo in os.listdir(path):
        if not arquivo.endswith(".csv"):
            continue

        # tente utf-8; se falhar, latin-1
        p = os.path.join(path, arquivo)
        try:
            df = pd.read_csv(p, delimiter=";")
        except UnicodeDecodeError:
            df = pd.read_csv(p, delimiter=";", encoding="latin-1")

        # muitos relatórios têm uma linha "TOTAL" no fim
        df = df.drop(index=df.index[-1], errors='ignore')

        # garantir que Número é string de dígitos (preserva zeros à esquerda)
        if 'Número' in df.columns:
            df['Número'] = df['Número'].astype(str).str.replace(r'\.0+$','', regex=True)

        # sempre comece com o mínimo
        colunas_validas = ['Candidato', 'Número', 'Votos']

        # Local de Votação (opcional, nem todo CSV tem)
        if 'Local de Votação' in df.columns:
            colunas_validas.append('Local de Votação')

        # Partido: já vem ou calculamos do prefixo do número
        if 'Partido' not in df.columns:
            if 'Número' in df.columns:
                df['Partido'] = df['Número'].apply(lambda x: meu_dict.get(str(x)[:2], ["Desconhecido"])[0])
        if 'Partido' in df.columns:
            colunas_validas.insert(1, 'Partido')  # após Candidato

        # Bairro/Regional (quando existir)
        if 'Bairro' in df.columns:
            # manter só o nome antes do " - " e tirar espaços
            df['Bairro'] = df['Bairro'].astype(str).str.split('-').str[0].str.strip()
            # normalizar caixa para chave do dicionário
            df['__BAIRRO_UC__'] = df['Bairro'].str.upper().str.strip()
            df['Regional'] = df['__BAIRRO_UC__'].map(bairro_para_regional)
            colunas_validas.extend(['Bairro', 'Regional'])

        # filtra apenas colunas existentes
        cols_existentes = [c for c in colunas_validas if c in df.columns]
        if not cols_existentes:
            continue

        df_u = df[cols_existentes].copy()

        # padroniza tipos
        if 'Votos' in df_u.columns:
            df_u['Votos'] = pd.to_numeric(df_u['Votos'], errors='coerce').fillna(0).astype(int)

        all_dfs.append(df_u)

    if not all_dfs:
        return pd.DataFrame(columns=['Candidato','Partido','Número','Local de Votação','Votos','Bairro','Regional'])

    out = pd.concat(all_dfs, ignore_index=True)

    # limpeza final
    if 'Regional' in out.columns:
        out['Regional'] = out['Regional'].fillna('Não mapeado')

    return out


df = carregar_dados()

# Interface
st.title("Votação Vereadores 2024 - Fortaleza")

modo = st.radio("Escolha o tipo de análise:", ["🔍 Por Local de Votação", "🗺️ Por Regional","🏘️ Por Bairro", "👤 Por Candidato"])

if modo == "🔍 Por Local de Votação":
    locais = sorted(df['Local de Votação'].dropna().unique()) if 'Local de Votação' in df.columns else []
    local_escolhido = st.selectbox("Selecione o Local:", locais)

    if local_escolhido:
        df_filtrado = df[df['Local de Votação'] == local_escolhido].copy()
        if not df_filtrado.empty:
            if 'Bairro' in df_filtrado.columns:
                bairro = df_filtrado['Bairro'].dropna().astype(str).unique()
                bairro = bairro[0] if len(bairro) else '—'
            else:
                bairro = '—'
            if 'Regional' in df_filtrado.columns:
                regional = df_filtrado['Regional'].dropna().astype(str).unique()
                regional = regional[0] if len(regional) else '—'
            else:
                regional = '—'
            st.markdown(f" Bairro: **{bairro}**  -  Regional: **{regional}** ")

        
elif modo == "🗺️ Por Regional":
    if "Bairro" not in df.columns:
        st.error("⚠️ A coluna 'Bairro' não existe nos seus arquivos.")
        
    else:
        regionais = sorted(df['Regional'].dropna().unique())
        regional_escolhida = st.selectbox("Selecione a Regional:", regionais)
        
        if regional_escolhida:
            df_filtrado = df[df['Regional'] == regional_escolhida]
               
elif modo == "🏘️ Por Bairro":
    if "Bairro" not in df.columns:
        st.error("⚠️ A coluna 'Bairro' não existe nos seus arquivos.")
        
    else:
        bairros = sorted(df['Bairro'].dropna().unique())
        bairro_escolhido = st.selectbox("Selecione o Bairro:", bairros)
        
        if bairro_escolhido:
            df_filtrado = df[df['Bairro'] == bairro_escolhido]
            regional = df_filtrado['Regional'].unique()[0]
            st.markdown(f" O bairro selecionado pertence a regional: {regional} ")
            
elif modo == "👤 Por Candidato":
    candidatos = sorted(df['Candidato'].dropna().unique())
    #index=384
    candidato_escolhido = st.selectbox("Selecione o Candidato:", candidatos)
    
    if candidato_escolhido:
        df_filtrado = df[df['Candidato'] == candidato_escolhido]
        
# Exibição de resultados
if 'df_filtrado' in locals() and not df_filtrado.empty:
    agrupado = None

    if modo == "👤 Por Candidato":
        group_cols = ['Local de Votação']
        if 'Bairro' in df_filtrado.columns: group_cols.append('Bairro')
        if 'Regional' in df_filtrado.columns: group_cols.append('Regional')

        agrupado = (
            df_filtrado
            .groupby(group_cols, dropna=False)['Votos']
            .sum()
            .reset_index()
            .sort_values(by='Votos', ascending=False)
        )
        total = int(agrupado['Votos'].sum())
        st.subheader(f"📍 Locais onde **{candidato_escolhido}** recebeu votos")
        st.markdown(f" 📈 O vereador **{candidato_escolhido}** recebeu **{total}** votos totais")

    else:
        agrupado = (
            df_filtrado
            .groupby([c for c in ['Candidato','Número','Partido'] if c in df_filtrado.columns], dropna=False)['Votos']
            .sum()
            .reset_index()
            .sort_values(by='Votos', ascending=False)
        )
        st.subheader("🏆 Vereador mais votado:")
        if not agrupado.empty:
            mais_votado = agrupado.iloc[0]
            nm = mais_votado.get('Candidato', '—')
            num = mais_votado.get('Número', '—')
            v = int(mais_votado['Votos'])
            st.markdown(f"**{nm}** ({num}) com **{v}** votos.")
            agrupado = agrupado[[c for c in ['Candidato','Partido','Votos'] if c in agrupado.columns]]

    # Tabela
    st.subheader("📋 Tabela de Votos")
    agrupado['Votos'] = agrupado['Votos'].astype(int)

    gb = GridOptionsBuilder.from_dataframe(agrupado)
    gb.configure_default_column(editable=False, resizable=False, filterable=False)
    if 'Votos' in agrupado.columns:
        gb.configure_column('Votos', editable=False, resizable=False, maxWidth=100, filter=False,
                            cellStyle={'textAlign': 'left'}, headerClass='ag-left-aligned-header')
    if modo == "👤 Por Candidato":
        if 'Bairro' in agrupado.columns:
            gb.configure_column('Bairro', editable=False, resizable=False, maxWidth=200, filter=False,
                                cellStyle={'textAlign': 'left'}, headerClass='ag-left-aligned-header')
        if 'Regional' in agrupado.columns:
            gb.configure_column('Regional', editable=False, resizable=False, maxWidth=200, filter=False,
                                cellStyle={'textAlign': 'left'}, headerClass='ag-left-aligned-header')

    grid_options = gb.build()
    AgGrid(agrupado, gridOptions=grid_options, height=615, fit_columns_on_grid_load=True)
elif 'df_filtrado' in locals():
    st.warning("Nenhum dado encontrado.")

