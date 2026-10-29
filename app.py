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

    # Интерактивная зона (теперь наполняем её компонентами)
    html.Div(id='dashboard-content', style={'display': 'none'}, children=[
        
        # Строка с выпадающим списком (Dropdown) для фильтрации данных
        dbc.Row(dbc.Col([
            html.Label("Фильтрация по категориям грузов:", className="text-white-50"),
            dcc.Dropdown(id='category-dropdown', multi=True, className="text-dark")
        ], width=6, className="mb-4")),

        # Блок из трех карточек-индикаторов (KPI) для ключевых метрик склада
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([html.H5("Общая выручка", className="card-title text-muted"), html.H3(id="kpi-revenue", className="text-success")]), color="dark"), width=4),
            dbc.Col(dbc.Card(dbc.CardBody([html.H5("Общие расходы", className="card-title text-muted"), html.H3(id="kpi-expenses", className="text-danger")]), color="dark"), width=4),
            dbc.Col(dbc.Card(dbc.CardBody([html.H5("Чистая прибыль", className="card-title text-muted"), html.H3(id="kpi-profit", className="text-info")]), color="dark"), width=4),
        ], className="mb-4"),

        # Первый блок графиков: Линейный временной ряд и Круговая диаграмма
        dbc.Row([
            dbc.Col(dcc.Graph(id='time-series-graph'), width=7),
            dbc.Col(dcc.Graph(id='pie-chart'), width=5)
        ], className="mb-4"),

        # Второй блок графиков: Гистограмма распределения и Диаграмма рассеяния
        dbc.Row([
            dbc.Col(dcc.Graph(id='histogram-graph'), width=6),
            dbc.Col(dcc.Graph(id='scatter-graph'), width=6)
        ], className="mb-4"),

        # Интерактивная таблица с возможностью постраничного просмотра данных
        dbc.Row(dbc.Col([
            html.H4("Детализированные данные склада за период", className="text-info mb-3"),
            dash_table.DataTable(
                id='data-table',
                style_table={'overflowX': 'auto'},
                style_header={'backgroundColor': '#111', 'color': '#0dcaf0', 'fontWeight': 'bold'},
                style_cell={'backgroundColor': '#222', 'color': 'white', 'textAlign': 'left'},
                page_size=5
            )
        ]))
    ])
], fluid=True) # ВОТ ЭТА СТРОКА БЫЛА УДАЛЕНА И СЕЙЧАС ИСПРАВЛЕНА

# --- Раздел интерактивных функций (Callbacks) ---

# Коллбэк №1: Обработка загрузки файла и активация интерфейса
@app.callback(
    Output('stored-data', 'data'),
    Output('category-dropdown', 'options'),
    Output('category-dropdown', 'value'),
    Output('dashboard-content', 'style'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_output(contents, filename):
    if contents is None:
        return {}, [], [], {'display': 'none'}
    
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    
    categories = df['Category'].unique()
    options = [{'label': i, 'value': i} for i in categories]
    
    return df.to_dict('records'), options, list(categories), {'display': 'block'}

# Коллбэк №2: Фильтрация данных и динамическое обновление графиков
@app.callback(
    Output('kpi-revenue', 'children'),
    Output('kpi-expenses', 'children'),
    Output('kpi-profit', 'children'),
    Output('time-series-graph', 'figure'),
    Output('pie-chart', 'figure'),
    Output('histogram-graph', 'figure'),
    Output('scatter-graph', 'figure'),
    Output('data-table', 'data'),
    Output('data-table', 'columns'),
    Input('stored-data', 'data'),
    Input('category-dropdown', 'value')
)
def update_dashboard(stored_records, selected_categories):
    if not stored_records:
        return "", "", "", go.Figure(), go.Figure(), go.Figure(), go.Figure(), [], []
    
    df = pd.DataFrame(stored_records)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df[df['Category'].isin(selected_categories)].sort_values('Date')

    # Расчет KPI
    total_rev = f"{df['Revenue'].sum():,.0f} ₽"
    total_exp = f"{df['Expenses'].sum():,.0f} ₽"
    total_prof = f"{df['Profit'].sum():,.0f} ₽"

    # График 1: Временной ряд доходов и расходов
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(x=df['Date'], y=df['Revenue'], name='Выручка', mode='lines+markers', line=dict(color='#198754')))
    fig_line.add_trace(go.Scatter(x=df['Date'], y=df['Expenses'], name='Расходы', mode='lines+markers', line=dict(color='#dc3545')))
    fig_line.update_layout(title="Динамика доходов и расходов склада", template="plotly_dark", xaxis_title="Дата", yaxis_title="Рубли")

    # График 2: Структура расходов (Круговая)
    fig_pie = px.pie(df, values='Expenses', names='Category', title='Structure of Expenses', template="plotly_dark")

    # График 3: Распределение чистой прибыли (Гистограмма)
    fig_hist = px.histogram(df, x='Profit', title='Распределение чистой прибыли', template="plotly_dark", color_discrete_sequence=['#0dcaf0'])
    fig_hist.update_layout(xaxis_title="Интервал прибыли", yaxis_title="Частота")

    # График 4: Зависимость объема груза и чистой прибыли (Рассеяние)
    fig_scatter = px.scatter(df, x='Volume_m3', y='Profit', color='Category', size='Revenue',
                             title='Корреляция: Объем хранения (м³) / Прибыль', template="plotly_dark")
    fig_scatter.update_layout(xaxis_title="Занятый объем склада (м³)", yaxis_title="Прибыль (₽)")

    # Подготовка таблицы
    df_str = df.copy()
    df_str['Date'] = df_str['Date'].dt.strftime('%Y-%m-%d')
    table_data = df_str.to_dict('records')
    table_columns = [{"name": i, "id": i} for i in df_str.columns]

    return total_rev, total_exp, total_prof, fig_line, fig_pie, fig_hist, fig_scatter, table_data, table_columns

# Запуск локального сервера
if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
# --- Раздел интерактивных функций (Callbacks) ---

# Коллбэк №1: Обработка загрузки файла и активация интерфейса
@app.callback(
    Output('stored-data', 'data'),
    Output('category-dropdown', 'options'),
    Output('category-dropdown', 'value'),
    Output('dashboard-content', 'style'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_output(contents, filename):
    if contents is None:
        return {}, [], [], {'display': 'none'}
    
    # Расшифровка base64 строки, полученной из браузера при загрузке
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    # Чтение данных в объект DataFrame библиотеки pandas
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    
    # Формирование списка уникальных категорий для выпадающего меню
    categories = df['Category'].unique()
    options = [{'label': i, 'value': i} for i in categories]
    
    # Возвращаем данные в хранилище, заполняем фильтр и делаем дашборд видимым
    return df.to_dict('records'), options, list(categories), {'display': 'block'}

# Коллбэк №2: Фильтрация данных и динамическое обновление графиков
@app.callback(
    Output('kpi-revenue', 'children'),
    Output('kpi-expenses', 'children'),
    Output('kpi-profit', 'children'),
    Output('time-series-graph', 'figure'),
    Output('pie-chart', 'figure'),
    Output('histogram-graph', 'figure'),
    Output('scatter-graph', 'figure'),
    Output('data-table', 'data'),
    Output('data-table', 'columns'),
    Input('stored-data', 'data'),
    Input('category-dropdown', 'value')
)
def update_dashboard(stored_records, selected_categories):
    if not stored_records:
        return "", "", "", go.Figure(), go.Figure(), go.Figure(), go.Figure(), [], []
    
    # Восстановление таблицы из хранилища и фильтрация по выбранным категориям грузов
    df = pd.DataFrame(stored_records)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df[df['Category'].isin(selected_categories)].sort_values('Date')

    # Расчет агрегированных метрик для карточек KPI
    total_rev = f"{df['Revenue'].sum():,.0f} ₽"
    total_exp = f"{df['Expenses'].sum():,.0f} ₽"
    total_prof = f"{df['Profit'].sum():,.0f} ₽"

    # График 1: Временной ряд доходов и расходов
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(x=df['Date'], y=df['Revenue'], name='Выручка', mode='lines+markers', line=dict(color='#198754')))
    fig_line.add_trace(go.Scatter(x=df['Date'], y=df['Expenses'], name='Расходы', mode='lines+markers', line=dict(color='#dc3545')))
    fig_line.update_layout(title="Динамика доходов и расходов склада", template="plotly_dark", xaxis_title="Дата", yaxis_title="Рубли")

    # График 2: Структура расходов по категориям (Круговая)
    fig_pie = px.pie(df, values='Expenses', names='Category', title='Структура расходов по категориям', template="plotly_dark")

    # График 3: Распределение чистой прибыли (Гистограмма)
    fig_hist = px.histogram(df, x='Profit', title='Распределение чистой прибыли', template="plotly_dark", color_discrete_sequence=['#0dcaf0'])
    fig_hist.update_layout(xaxis_title="Интервал прибыли", yaxis_title="Частота (кол-во операций)")

    # График 4: Корреляция объема груза в м3 и прибыли (Диаграмма рассеяния)
    fig_scatter = px.scatter(df, x='Volume_m3', y='Profit', color='Category', size='Revenue',
                             title='Корреляция: Объем хранения (м³) / Прибыль', template="plotly_dark")
    fig_scatter.update_layout(xaxis_title="Занятый объем склада (м³)", yaxis_title="Прибыль (₽)")

    # Преобразование формата дат для корректного отображения внутри таблицы данных
    df_str = df.copy()
    df_str['Date'] = df_str['Date'].dt.strftime('%Y-%m-%d')
    table_data = df_str.to_dict('records')
    table_columns = [{"name": i, "id": i} for i in df_str.columns]

    return total_rev, total_exp, total_prof, fig_line, fig_pie, fig_hist, fig_scatter, table_data, table_columns

# Системный блок для автоматического запуска локального веб-сервера
if __name__ == '__main__':
    app.run(debug=True, port=8050)
