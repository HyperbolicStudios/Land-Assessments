import os
from inspect import getsourcefile
from os.path import abspath

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

import plotly.express as px
import chart_studio
#set active directory to file location
directory = abspath(getsourcefile(lambda:0))
#check if system uses forward or backslashes for writing directories
if(directory.rfind("/") != -1):
    newDirectory = directory[:(directory.rfind("/")+1)]
else:
    newDirectory = directory[:(directory.rfind("\\")+1)]
os.chdir(newDirectory)

oak_bay_data = pd.read_csv('data/2023 Oak Bay.csv')

#import oak bay properties
properties = gpd.read_file('data/oak_bay_properties.geojson')



def generate_maps(properties, assessments_df):

    #ge`opandas - show all data when calling head
    #pd.set_option('display.max_columns', None)

    #make address all upercase
    properties['StreetName'] = properties['StreetName'].str.upper()
    #create pd column of Address Combined that combined StreetNumber and StreetName
    properties['AddressCombined'] = properties['StreetNumber'].astype(str) + ' ' + properties['StreetName']

    #print number of rows
    print('Number of rows: ' + str(len(properties.index)))
    #reduce df to just AddressCombined, City and geometry
    properties = properties[[ 'City', 'AddressCombined',  'geometry']]

    #dissolve shapes with the same AddressCombined
    properties = properties.dissolve(by='AddressCombined')

    #print number of rows
    print('Number of rows: ' + str(len(properties.index)))
    
    #dissolve assessment_df by Situs Street Address, sum the Actual Value Land Total and Actual Value Total columns, and keep all other columns as first
    assessments_df = assessments_df.groupby('Situs Street Address').agg({'Actual Value Land Total': 'sum', 'Actual Value Total': 'sum'}).reset_index()

    #merge with oak bay data on AddressCombined and Situs Street Address
    data = properties.merge(assessments_df, left_on='AddressCombined', right_on='Situs Street Address', how='left')
    data = data.rename(columns={'Situs Street Address': 'Address'})

    #convert to UTM zone 10n crs
    data = data.to_crs("32610")

    #create column Area1 that is the area of the polygon
    data['Area'] = data['geometry'].area

    #create landval-per-area column and round the result

    data['LandValperArea'] = (data['Actual Value Land Total'] / data['Area']).round(0)

    data['TotalValperArea'] = (data['Actual Value Total'] / data['Area']).round(0)
    data['Area'] = data['Area'].round(0)

    #make address Title Case
    data['Address'] = data['Address'].str.title()
    #convert to wgs 84 (Required for mapping with plotly)
    data = data.to_crs("EPSG:4326")

    def map(data, colorby):
        fig = px.choropleth_mapbox(data, geojson=data.geometry, locations=data.index, color=colorby,
                                            color_continuous_scale="Viridis",
                                            range_color=(1000, 4000),
                                            mapbox_style="carto-positron",

                                            zoom=12, center = {"lat":  48.431699, "lon": -123.319873},
                                            opacity=.5,
                                            custom_data = ['Address','Area','Actual Value Land Total','Actual Value Total','LandValperArea','TotalValperArea']
                                            )

        fig.update_traces(marker_line_width=.01,
                        hovertemplate = """
                        <b>%{customdata[0]}</b><br>
                        <b>Area: </b>%{customdata[1]} M2 <br>
                        <b>Land Value: </b>%{customdata[2]} $ <br>
                        <b>Total Value: </b>%{customdata[3]} $ <br>
                        <b>Land Value per M2: </b> %{customdata[4]} $/M2 <br>
                        <b>Total Value per M2: </b> %{customdata[5]} $/M2"""
                                                        )
        #remove margin around plot
        fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
    
        return(fig)
    fig = map(data, 'TotalValperArea')
    fig.update_layout(coloraxis_colorbar=dict(title="Value/M2"))

    #export to html
    fig.write_html("total_values_per_m2.html")

    fig = map(data, 'LandValperArea')
    fig.update_layout(coloraxis_colorbar=dict(title="Value/M2"))

    #export to html
    fig.write_html("land_values_per_m2.html")

generate_maps(properties, oak_bay_data)