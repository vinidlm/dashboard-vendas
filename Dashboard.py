import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(layout='wide')

def formata_num(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'

st.title('DASHBOARD VENDAS :shopping_trolley:')

url = 'https://labdados.com/produtos'
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']
st.sidebar.title('Filtros')

regiao = st.sidebar.selectbox('Região', regioes)
if regiao == 'Brasil':
    regiao = ''
    
anos = st.sidebar.checkbox('Dados de todo o período', value=True)
if anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)
    
query_str = {'regiao':regiao.lower(), 'ano':ano}

response = requests.get(url, params=query_str)
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

#Tabelas
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()
receita_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(receita_estados, left_on = 'Local da compra', right_index=True).sort_values('Preço',ascending=False)

receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()

receita_cat = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)

vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))


#Graficos
fig_map_receita = px.scatter_geo(receita_estados,
                                 lat='lat', lon='lon',
                                 scope='south america',
                                 size = 'Preço',
                                 template = 'seaborn',
                                 hover_name = 'Local da compra',
                                 hover_data = {'lat': False, 'lon':False},
                                 title = 'Receita por Estado')

fig_receita_men = px.line(receita_mensal,
                          x='Mes',
                          y='Preço',
                          markers = True,
                          range_y = (0, receita_mensal.max()),
                          color = 'Ano',
                          line_dash = 'Ano',
                          title = 'Receita Mensal')
fig_receita_men.update_layout(yaxis_title = 'Receita')

fig_receita_estados = px.bar(receita_estados.head(),
                             x='Local da compra', y='Preço',
                             text_auto = True,
                             title = 'Top estados')
fig_receita_estados.update_layout(yaxis_title = 'Receita')

fig_receita_cat = px.bar(receita_cat,
                         text_auto = True,
                         title = 'Receita por Categoria')
fig_receita_cat.update_layout(yaxis_title = 'Receita')

#Visualização no Streamlit
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de Vendas', 'Vendedores'])

with aba1:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_num(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_map_receita, use_container_width = True)
        st.plotly_chart(fig_receita_estados, use_container_width = True)

    with coluna2:
        st.metric('Quantidade de vendas', formata_num(dados.shape[0]))
        st.plotly_chart(fig_receita_men, use_container_width = True)
        st.plotly_chart(fig_receita_cat, use_container_width = True)
 
with aba2:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_num(dados['Preço'].sum(), 'R$'))

    with coluna2:
        st.metric('Quantidade de vendas', formata_num(dados.shape[0]))


with aba3:
    qtd_vendedores = st.number_input('Quantidade de Vendedores', 2, 10, 5)
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_num(dados['Preço'].sum(), 'R$'))
        fig_vend = px.bar(vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores),
                          x='sum', 
                          y=vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores).index,
                          text_auto=True,
                          title = f'Top {qtd_vendedores} vendedores')
        st.plotly_chart(fig_vend, use_container_width = True)

    with coluna2:
        st.metric('Quantidade de vendas', formata_num(dados.shape[0]))
        fig_vendas = px.bar(vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores),
                        x='count', 
                        y=vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores).index,
                        text_auto=True,
                        title = f'Top {qtd_vendedores} vendedores (quantidade de vendas)')
        st.plotly_chart(fig_vendas, use_container_width = True)



