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
        conteudo = f.read()
        meu_dict = ast.literal_eval(conteudo)
        
    with open('lista_regionais.txt', "r", encoding="utf-8") as f:
        conteudo_regional = f.read()
        regionais_dict = ast.literal_eval(conteudo_regional)
      
    bairro_para_regional = {
        bairro.upper().strip(): regional
        for regional, bairros in regionais_dict.items()
        for bairro in bairros
    }   
  
    for arquivo in os.listdir(path):
        if arquivo.endswith(".csv"):
            df = pd.read_csv(os.path.join(path, arquivo), delimiter=";")
            df = df.drop(index=df.index[-1], errors='ignore')
            df['Número'] = df['Número'].astype(int)
            df['Número'] = df['Número'].astype(str)

            if "Partido" not in df.columns:
                    df["Partido"] = df["Número"].apply(lambda x: meu_dict.get(x[:2], ["Desconhecido"])[0])
                            
                    colunas_validas = ['Candidato', 'Partido', 'Número', 'Local de Votação', 'Votos']
            if 'Bairro' in df.columns:
                    df['Bairro'] = df['Bairro'].str.split('-').str[0]
                    df['Regional'] = df['Bairro'].map(bairro_para_regional)
                    colunas_validas.extend(['Bairro', 'Regional'])
            df_u = df[colunas_validas]
            
            all_dfs.append(df_u)
            
    return pd.concat(all_dfs, ignore_index=True)

df = carregar_dados()

# Interface
st.title("Votação Vereadores 2024 - Fortaleza")

modo = st.radio("Escolha o tipo de análise:", ["🔍 Por Local de Votação", "🗺️ Por Regional","🏘️ Por Bairro", "👤 Por Candidato"])

if modo == "🔍 Por Local de Votação":
    locais = sorted(df['Local de Votação'].dropna().unique())
    local_escolhido = st.selectbox("Selecione o Local:", locais)

    if local_escolhido:
        df_filtrado = df[df['Local de Votação'] == local_escolhido]
        bairro = df_filtrado['Bairro'].unique()[0]
        regional = df_filtrado['Regional'].unique()[0]
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
        agrupado = df_filtrado.groupby(['Local de Votação','Bairro','Regional'])['Votos'].sum().reset_index() 
        agrupado = agrupado.sort_values(by='Votos', ascending=False)
        total = agrupado['Votos'].sum()
        st.subheader(f"📍 Locais onde **{candidato_escolhido}** recebeu votos")
        st.markdown(f" 📈 O vereador **{candidato_escolhido}** recebeu **{total}** votos totais")
  
    else:
        agrupado = df_filtrado.groupby(['Candidato', 'Número', 'Partido'])['Votos'].sum().reset_index()
        agrupado = agrupado.sort_values(by='Votos', ascending=False)
        st.subheader("🏆 Vereador mais votado:")
        mais_votado = agrupado.iloc[0]
        st.markdown(f"**{mais_votado['Candidato']}** ({mais_votado['Número']}) com **{mais_votado['Votos']}** votos.")
        agrupado = agrupado[['Candidato', 'Partido', 'Votos']]

    # Tabela
    st.subheader("📋 Tabela de Votos") 
    agrupado['Votos'] = agrupado['Votos'].astype(int)
    botao_excel = 0
    botao_pdf = 0
    
    gb = GridOptionsBuilder.from_dataframe(agrupado)
    gb.configure_default_column(editable=False, resizable=False, filterable= False)
    gb.configure_column('Votos', editable=False, resizable=False, maxWidth= 100, filter= False, cellStyle={'textAlign': 'left'}, headerClass='ag-left-aligned-header')
    if modo == "👤 Por Candidato":
        gb.configure_column('Bairro', editable=False, resizable=False, maxWidth= 200, filter= False, cellStyle={'textAlign': 'left'}, headerClass='ag-left-aligned-header') 
        gb.configure_column('Regional', editable=False, resizable=False, maxWidth= 200, filter= False, cellStyle={'textAlign': 'left'}, headerClass='ag-left-aligned-header')   
    grid_options = gb.build()

    AgGrid(agrupado, gridOptions=grid_options,height= 615,fit_columns_on_grid_load=True)
    
elif 'df_filtrado' in locals():
    st.warning("Nenhum dado encontrado.")
