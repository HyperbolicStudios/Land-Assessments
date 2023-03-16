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

#geopandas - show all data when calling head
#pd.set_option('display.max_columns', None)

#make address all upercase
properties['StreetName'] = properties['StreetName'].str.upper()
#create pd column of Address Combined that combined StreetNumber and StreetName
properties['AddressCombined'] = properties['StreetNumber'].astype(str) + ' ' + properties['StreetName']

#reduce df to just AddressCombined, PostalCode, City and geometry
properties = properties[[ 'City','PostalCode', 'AddressCombined',  'geometry']]

#merge with oak bay data on AddressCombined and Situs Street Address
data = properties.merge(oak_bay_data, left_on='AddressCombined', right_on='Situs Street Address', how='left')
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

fig = px.choropleth_mapbox(data, geojson=data.geometry, locations=data.index, color="TotalValperArea",
                                       color_continuous_scale="Viridis",
                                       range_color=(1000, 4000),
                                       mapbox_style="carto-positron",

                                       zoom=10, center = {"lat":  48.431699, "lon": -123.319873},
                                       opacity=.5,
                                       custom_data = ['Address','Area','Actual Value Land Total','Actual Value Total','LandValperArea','TotalValperArea']
                                       )

fig.update_traces(hovertemplate = """
                <b>%{customdata[0]}</b><br>
                <b>Area: </b>%{customdata[1]} M2 <br>
                <b>Land Value: </b>%{customdata[2]} $ <br>
                <b>Total Value: </b>%{customdata[3]} $ <br>
                <b>Land Value per M2: </b> %{customdata[4]} $/M2 <br>
                <b>Total Value per M2: </b> %{customdata[5]} $/M2"""
                                                 )
#update legend name
fig.update_layout(coloraxis_colorbar=dict(title="Total Value per M2"))

#add title and center it
fig.update_layout(title_text='Oak Bay Property (Land and Improvement) Values per M2',title_x=0.5)

fig.to_html("index.html")