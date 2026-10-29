import base64
import io
import dash
from dash import dcc, html, dash_table, Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

# Инициализируем проект и подключаем тему оформления Cyborg (темный стиль)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
app.title = "Управление складом | Дашборд"

# Базовая разметка страницы
app.layout = dbc.Container([
    # Строка с главным заголовком приложения
    dbc.Row(dbc.Col(html.H1("Интерактивный дашборд: Процесс управления складом", 
                            className="text-center my-4 text-info"))),
    
    # Строка с компонентом для загрузки файлов через браузер
    dbc.Row(dbc.Col(
        dcc.Upload(
            id='upload-data',
            children=html.Div(['Перетащите сюда или ', html.A('выберите CSV-файл складирования')]),
            style={
                'width': '100%', 'height': '60px', 'lineHeight': '60px',
                'borderWidth': '2px', 'borderStyle': 'dashed', 'borderRadius': '10px',
                'textAlign': 'center', 'margin': '10px 0', 'backgroundColor': '#222'
            },
            multiple=False
        )
    )),
    
    # Невидимое хранилище в оперативной памяти браузера для сохранения табличных данных
    dcc.Store(id='stored-data'),

    # Будущая интерактивная зона (пока оставляем ее пустой и скрытой)
    html.Div(id='dashboard-content', style={'display': 'none'}, children=[
        # Сюда на следующем этапе мы вставим графики и таблицы
    ])
], fluid=True)
