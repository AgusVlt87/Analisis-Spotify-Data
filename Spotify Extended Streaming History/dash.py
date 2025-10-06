# =======================================================
# 🎛️ DASHBOARD INTERACTIVO - TU HISTORIAL DE SPOTIFY
# =======================================================

import json
import pandas as pd
import glob
from dash import Dash, dcc, html, Input, Output
import plotly.express as px

# =============================================
# CARGA Y PREPROCESAMIENTO
# =============================================
json_files = glob.glob('C:\\Spotify\\Analisis-Spotify-Data\\Spotify Extended Streaming History\\Streaming_History_Audio_*.json')

data = []
for file in json_files:
    with open(file, 'r', encoding='utf-8') as f:
        data.extend(json.load(f))

df = pd.DataFrame(data)
df['ts'] = pd.to_datetime(df['ts'])
df['minutes_played'] = df['ms_played'] / 60000
df = df[df['minutes_played'] > 0.5]
df['year'] = df['ts'].dt.year
df['month'] = df['ts'].dt.to_period('M').astype(str)
df['date'] = df['ts'].dt.date

# =============================================
# DASHBOARD
# =============================================
app = Dash(__name__)
app.title = "Tu Spotify Wrapped Personal"

# Dropdowns dinámicos
artists = sorted(df['master_metadata_album_artist_name'].dropna().unique())
platforms = sorted(df['platform'].dropna().unique())
years = sorted(df['year'].dropna().unique())

app.layout = html.Div([
    html.H1("🎧 Tu Spotify History Dashboard", style={'textAlign': 'center'}),

    html.Div([
        html.Div([
            html.Label('📅 Año:'),
            dcc.Dropdown(years, value=years[-1], id='year_filter', clearable=False)
        ], style={'width': '30%', 'display': 'inline-block'}),

        html.Div([
            html.Label('🎤 Artista:'),
            dcc.Dropdown(artists, value=None, id='artist_filter', placeholder='Todos', multi=True)
        ], style={'width': '35%', 'display': 'inline-block', 'marginLeft': '10px'}),

        html.Div([
            html.Label('💻 Plataforma:'),
            dcc.Dropdown(platforms, value=None, id='platform_filter', placeholder='Todas')
        ], style={'width': '30%', 'display': 'inline-block', 'marginLeft': '10px'})
    ], style={'margin': '20px'}),

    dcc.Graph(id='time_series'),
    dcc.Graph(id='top_artists'),
    dcc.Graph(id='heatmap')
])

# =============================================
# CALLBACKS INTERACTIVOS
# =============================================

@app.callback(
    [Output('time_series', 'figure'),
     Output('top_artists', 'figure'),
     Output('heatmap', 'figure')],
    [Input('year_filter', 'value'),
     Input('artist_filter', 'value'),
     Input('platform_filter', 'value')]
)
def update_dashboard(selected_year, selected_artists, selected_platform):
    dff = df.copy()
    dff = dff[dff['year'] == selected_year]
    if selected_platform:
        dff = dff[dff['platform'] == selected_platform]
    if selected_artists:
        dff = dff[dff['master_metadata_album_artist_name'].isin(selected_artists)]

    # Serie temporal mensual
    monthly = dff.groupby('month')['minutes_played'].sum().reset_index()
    fig1 = px.line(monthly, x='month', y='minutes_played',
                   title='⏱️ Minutos escuchados por mes',
                   markers=True, line_shape='spline')

    # Top artistas
    top_art = (
        dff.groupby('master_metadata_album_artist_name')['minutes_played']
          .sum().sort_values(ascending=False).head(10).reset_index()
    )
    fig2 = px.bar(top_art, x='minutes_played', y='master_metadata_album_artist_name',
                  orientation='h', title='🏆 Artistas más escuchados')

    # Heatmap de día/hora
    dff['weekday'] = dff['ts'].dt.day_name()
    dff['hour'] = dff['ts'].dt.hour
    heatmap_data = dff.groupby(['weekday', 'hour'])['minutes_played'].sum().reset_index()
    heatmap_data['weekday'] = pd.Categorical(
        heatmap_data['weekday'],
        categories=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'],
        ordered=True
    )
    fig3 = px.density_heatmap(heatmap_data, x='hour', y='weekday', z='minutes_played',
                              color_continuous_scale='magma',
                              title='🔥 Cuándo escuchás más música')

    fig1.update_layout(template='plotly_dark')
    fig2.update_layout(template='plotly_dark')
    fig3.update_layout(template='plotly_dark')

    return fig1, fig2, fig3

# =============================================
# EJECUTAR APP
# =============================================
if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
