from logging.config import fileConfig
from turtle import update
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


df_plants = pd.read_csv('Renewable_Power_Plants_100.csv')       
df_time_series = pd.read_csv('Time_Series_PV.csv')               
df_weather = pd.read_csv('Weather_Data_PV.csv')                
df_pv_profiles = pd.read_csv('Renewables_ninja_PV_Profiles.csv') 


df_time_series['DateTime'] = pd.to_datetime(df_time_series['DateTime'])
df_weather['DateTime'] = pd.to_datetime(df_weather['DateTime'])
df_pv_profiles['DateTime'] = pd.to_datetime(df_pv_profiles['DateTime'])



df_merged = pd.merge(df_time_series, df_weather, on='DateTime', how='left')
df_full = pd.merge(df_merged, df_pv_profiles, on='DateTime', how='left')


df_full['Efficiency_Calc'] = df_full['Actual_Production'] / df_full['Theoretical_Production_W'] * 100


station_names = df_plants['System_Name'].tolist() 
df_full['System_Name'] = [station_names[i % len(station_names)] for i in range(len(df_full))]



df_full['Date'] = df_full['DateTime'].dt.date
df_full['Month'] = df_full['DateTime'].dt.to_period('M')

daily_summary = df_full.groupby(['System_Name','Date']).agg({
    'Actual_Production':'sum',
    'Theoretical_Production_W':'sum',
    'Efficiency_Calc':'mean',
    'Irradiance_W_m2':'mean',
    'Temperature_C':'mean',
    'Cloudiness_%':'mean'
}).reset_index()

monthly_summary = df_full.groupby(['System_Name','Month']).agg({
    'Actual_Production':'sum',
    'Theoretical_Production_W':'sum',
    'Efficiency_Calc':'mean'
}).reset_index()


fig = make_subplots(
    rows=5, cols=1,
    shared_xaxes=False,
    vertical_spacing=0.05,
    subplot_titles=(
        "Actual Production", 
        "Theoretical Production",
        "Efficiency vs Irradiance",
        "Temperature & Cloudiness",
        "Daily Efficiency"
    )
)


for i, station in enumerate(station_names):
    df_station = df_full[df_full['System_Name']==station]
    df_daily = daily_summary[daily_summary['System_Name']==station]
    

    fig.add_trace(go.Scatter(x=df_station['DateTime'], y=df_station['Actual_Production'],
                             mode='lines', name=f'{station} Actual', visible=(i==0)), row=1, col=1)
    
  
    fig.add_trace(go.Scatter(x=df_station['DateTime'], y=df_station['Theoretical_Production_W'],
                             mode='lines', name=f'{station} Theoretical', visible=(i==0)), row=2, col=1)
    
  
    fig.add_trace(go.Scatter(x=df_station['Irradiance_W_m2'], y=df_station['Efficiency_Calc'],
                             mode='markers', name=f'{station} Eff vs Irradiance', visible=(i==0)), row=3, col=1)
    
   
    fig.add_trace(go.Scatter(x=df_station['DateTime'], y=df_station['Temperature_C'],
                             mode='lines', name=f'{station} Temperature', visible=(i==0)), row=4, col=1)
    fig.add_trace(go.Scatter(x=df_station['DateTime'], y=df_station['Cloudiness_%'],
                             mode='lines', name=f'{station} Cloudiness', visible=(i==0)), row=4, col=1)
    

    fig.add_trace(go.Scatter(x=df_daily['Date'], y=df_daily['Efficiency_Calc'],
                             mode='lines+markers', name=f'{station} Daily Efficiency', visible=(i==0)), row=5, col=1)

buttons = []
for i, station in enumerate(station_names):
    visibility = [False]*len(fig.data)
    for j in range(5):  
        visibility[i*5 + j] = True
        if j==3:  
            visibility[i*5 + j + 1] = True
    buttons.append(dict(label=station,
                        method="update",
                        args=[{"visible": visibility},
                              {"title": f"PV Dashboard for {station}"}]))

fig.update_layout(
    updatemenus=[dict(active=0, buttons=buttons)],
    height=1200,
    title=f"PV Dashboard for {station_names[0]}",
    xaxis1_title='Time',
    yaxis1_title='Power (W)',
    yaxis2_title='Power (W)',
    xaxis3_title='Irradiance',
    yaxis3_title='Efficiency (%)',
    yaxis4_title='Temperature / Cloudiness',
    xaxis5_title='Date',
    yaxis5_title='Daily Efficiency (%)'
)

fig.show()

fig update_layout(
    updatemenues=[])
