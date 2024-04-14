#!/usr/bin/env python
# coding: utf-8

import json, math, copy, sys, re
import csv
#from geosnap.data import store_ltdb
from geosnap.io import store_ltdb
#from geosnap.data import Community
from geosnap import Community, datasets
#from geosnap.data import store_census
from geosnap.io import store_census
#from geosnap.data import data_store
import pandas as pd
import shapely.wkt
import shapely.geometry
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from INCS import linc
import urllib.parse
import webbrowser
import os
import pprint
from sklearn.preprocessing import minmax_scale
#from sklearn.cluster import KMeans
import numpy as np
from scipy import stats
from IPython.core.display import display, HTML
import geopandas as gpd
###Comment out below to run in local env#########################################
from jupyter_server import serverapp

def Directory_vis(param):
    ###Comment out these to run in local env#########################################
    #Retrieve Server URL that Jupyter is running
    jupyter_envs = {k: v for k, v in os.environ.items() if k.startswith('JUPYTER')}
    temp_server = jupyter_envs['JUPYTER_INSTANCE_URL']
    
    ##Define Paths for Visualization (Jupyter Lab)
    servers = list(serverapp.list_running_servers())
    servers1 = temp_server+servers[0]["base_url"]+ 'view'
    servers2 = temp_server+servers[0]["base_url"]+ 'edit'
    #################################################################################
    
    cwd = os.getcwd()
    prefix_cwd = "/home/jovyan/work"
    cwd = cwd.replace(prefix_cwd, "")
    
    local_dir1 = cwd
    local_dir2 = cwd  
    
    ###This is for CyberGISX. Uncomment two command lines below when you run in CyberGIX Environment
    local_dir1 = servers1 + cwd + '/'
    local_dir2 = servers2 + cwd + '/'
    #################################################################################
    
    #local_dir = os.path.dirname(os.path.realpath(__file__))
    #print(local_dir)
    fname =urllib.parse.quote('index.html')
    template_dir = os.path.join(local_dir1, 'NAM_' + param['filename_suffix'])
    url = 'file:' + os.path.join(template_dir, fname)
    #print(url)
    webbrowser.open(url)
    
    print('To see your visualization, Click the URL below (or locate files):')
    print(url)
    #print('Please run ' + '"NAM_' + param['filename_suffix']+'/index.html"'+' to your web browser.')
    #print('Advanced options are available in ' +local_dir2 + 'NAM_' + param['filename_suffix']+'/data/GEO_CONFIG.js')
    print('Advanced options are available in ')  
    print(local_dir2 + 'NAM_' + param['filename_suffix']+'/data/GEO_CONFIG_' + param['filename_suffix']+'.js')

# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()


def to_csv_write(arrayName, standardization, nClusters, years, variables, array):
    csvfile = open("output_"+arrayName+".csv", 'w', newline='')
    csvwriter = csv.writer(csvfile)
    
    if arrayName == "zScore" or standardization == False:
        headers = ['Cluster'] + variables
        csvwriter.writerow(headers)
        for c in range(nClusters):
            cluster = "T" + str(c)
            record = [cluster] + [array[c][v] for v in range(len(array[c]))]
            csvwriter.writerow(record)
    
    if arrayName != "zScore" and standardization == True:
        headers = ['Cluster', 'Year'] + variables
        csvwriter.writerow(headers)
        for c in range(nClusters):
            cluster = "T" + str(c)
            for y, year in enumerate(years):
                record = [cluster, year] + [array[c][y][v] for v in range(len(array[c][y]))]
                csvwriter.writerow(record)
    
    csvfile.close()    


def write_LOG(param):
    #Create a new folder where GEO_CONFIG.js GEO_JSON.js VARIABLES.js will be saved
    oDir = 'NAM_' + param['filename_suffix']
    path = Path(oDir + '/data')
    path.mkdir(parents=True, exist_ok=True)
    
    contents = pprint.pformat(param)
    #print(oDir+"/data/param.log")
    #print(contents)
    #write new outfiles: GEO_CONFIG.js GEO_JSON.js VARIABLES.js
    ofile = open(oDir+"/data/param.log", "w")
    create_at = datetime.now()
    ofile.write('%s %s\r\n' % (create_at.strftime('%Y-%m-%d'), create_at.strftime('%H:%M:%S')))
    #ofile.write('\r\n\r\n')
    ofile.write('  '+contents.replace('\n', '\n  '))
    ofile.close()


def write_INDEX_html(param):
    #Create a new folder where GEO_CONFIG.js GEO_JSON.js VARIABLES.js will be saved
    oDir = 'NAM_' + param['filename_suffix']
    path = Path(oDir + '/data')
    path.mkdir(parents=True, exist_ok=True)
    
    contents = []
    #open Neighborhood_Analysis_Mapper.html (the excutable file for the visualization)
    ifile = open("template/Neighborhood_Analysis_Mapper.html", "r", encoding="utf-8")
    contents = ifile.read()
    
    #Replace variables based on the user's selection in each of four files below.
    contents = contents.replace("Neighborhood Analysis Mapper", param['title'])
    contents = contents.replace("data/GEO_CONFIG.js", "data/GEO_CONFIG_"+param['filename_suffix']+".js")
    contents = contents.replace("data/GEO_JSON.js", "data/GEO_JSON_"+param['filename_suffix']+".js")
    contents = contents.replace("data/GEO_VARIABLES.js", "data/GEO_VARIABLES_"+param['filename_suffix']+".js")
    
    #write new outfiles: GEO_CONFIG.js GEO_JSON.js VARIABLES.js
    ofile = open(oDir+"/index.html", "w", encoding="utf-8")
    ofile.write(contents)
    ofile.close()


def write_ALL_METROS_INDEX_html(param):
    #Create a new folder where GEO_CONFIG.js GEO_JSON.js VARIABLES.js will be saved
    oDir = 'NAM_' + param['filename_suffix']
    path = Path(oDir + '/data')
    path.mkdir(parents=True, exist_ok=True)
    
    contents = []
    #open Adaptive_Choropleth_Mapper.html (the excutable file for the visualization)
    ifile = open("template/Adaptive_Choropleth_Mapper.html", "r", encoding="utf-8" )
    contents = ifile.read()
    
    #Replace variables based on the user's selection in each of four files below.
    contents = contents.replace("Adaptive Choropleth Mapper", param['title'])
    contents = contents.replace("data/GEO_CONFIG.js", "data/GEO_CONFIG_"+param['filename_suffix']+".js")
    contents = contents.replace("data/GEO_JSON.js", "data/GEO_JSON_"+param['filename_suffix']+".js")
    contents = contents.replace("data/GEO_VARIABLES.js", "data/GEO_VARIABLES_"+param['filename_suffix']+".js")
    
    #write new outfiles: GEO_CONFIG.js GEO_JSON.js VARIABLES.js
    ofile = open(oDir+"/index.html", "w", encoding="utf-8")
    ofile.write(contents)
    ofile.close()


def write_GEO_CONFIG_js(param):
    # read ACM_GEO_CONFIG.js
    ifile = open("template/NAM_GEO_CONFIG.js", "r", encoding="utf-8")
    contents = ifile.read()
    SubjectName = "";
    allMetros = False;
    Index_of_neighborhood_change = False;
    Qualitative_Maps = True;
    Distribution_INC1 = False;
    Distribution_period = False; 
    Distribution_cluster = False;
    standardization = False;
    Stacked_Chart = False;
    Transition_Chart = False;
    Parallel_Categories_Diagram = False;
    Chord_Diagram = False;
    HeatmapTitle = "";
    Heatmap = False;
    Horizontal_Bar_Title = "";    
    HorizonalBarChart = False;
    
    if ('SubjectName' in param): SubjectName =  param['SubjectName']
    if ('allMetros' in param): allMetros =  param['allMetros']
    if ('Index_of_neighborhood_change' in param): Index_of_neighborhood_change =  param['Index_of_neighborhood_change']
    if ('Qualitative_Maps' in param): Qualitative_Maps =  param['Qualitative_Maps']
    if ('Distribution_INC1' in param): Distribution_INC1 =  param['Distribution_INC1']
    if ('Distribution_INC2_different_period' in param): Distribution_period =  param['Distribution_INC2_different_period']
    if ('Distribution_INC2_different_cluster' in param): Distribution_cluster =  param['Distribution_INC2_different_cluster']
    if ('standardization' in param): standardization =  param['standardization']
    if ('Stacked_Chart' in param): Stacked_Chart =  param['Stacked_Chart']
    if ('Transition_Chart' in param): Transition_Chart =  param['Transition_Chart']
    if ('Parallel_Categories_Diagram' in param): Parallel_Categories_Diagram =  param['Parallel_Categories_Diagram']
    if ('Chord_Diagram' in param): Chord_Diagram =  param['Chord_Diagram']
    if ('HeatmapTitle' in param): HeatmapTitle =  param['HeatmapTitle']
    if ('Heatmap' in param): Heatmap =  param['Heatmap']
    if ('Horizontal_Bar_Title' in param): Horizontal_Bar_Title =  param['Horizontal_Bar_Title']
    if ('HorizonalBarChart' in param): HorizonalBarChart =  param['HorizonalBarChart']
    
    # perpare parameters
    #NumOfMaps = len(param['years']) + 1
    NumOfMaps = len(param['years']) + 1 if Index_of_neighborhood_change else len(param['years'])
    #InitialLayers = ["INC"]
    InitialLayers = ["INC"] if Index_of_neighborhood_change else []
    if (len(param['years']) <= 1): InitialLayers = []
    for i, year in enumerate(param['years']):
        InitialLayers.append(str(year))
    
    # Automatically set Map_width, Map_height. 
    Map_width = "300px"
    Map_height = "300px"
    if (NumOfMaps <= 6):
        Map_width = "300px"
        Map_height = "300px"	
    if (NumOfMaps <= 5):
        Map_width = "350px"
        Map_height = "350px"
    if (NumOfMaps <= 4):
        Map_width = "400px"
        Map_height = "400px"
    if (NumOfMaps <= 3):
        Map_width = "400px"
        Map_height = "400px"
    if (NumOfMaps <= 2):
        Map_width = "450px"
        Map_height = "450px"
    if (NumOfMaps ==	1):
        Map_width = "800px"
        Map_height = "800px"	
    # replace newly computed "NumOfMaps", "InitialLayers", "Map_width", "Map_height" in CONFIG.js. See the example replacement below
    '''
        'years': [1980, 1990, 2000, 2010]            ->    'var InitialLayers = ["INC", "1980", "1990", "2000", "2010"];'
    '''
    NumOfMaps = "var NumOfMaps = " + str(NumOfMaps) + ";"
    SubjectName = 'var SubjectName = "' + str(SubjectName) + '";'
    InitialLayers = "var InitialLayers = " + json.dumps(InitialLayers) + ";"
    allMetros = "var allMetros = " + json.dumps(allMetros)+ ";"
    Index_of_neighborhood_change = "var Index_of_neighborhood_change = " + json.dumps(Index_of_neighborhood_change)+ ";"
    Qualitative_Maps = "var Qualitative_Maps = " + json.dumps(Qualitative_Maps)+ ";"
    Distribution_INC1 = "var Distribution_INC1 = " + json.dumps(Distribution_INC1)+ ";"
    Distribution_period = "var Distribution_INC2_different_period = " + json.dumps(Distribution_period)+ ";"
    Distribution_cluster = "var Distribution_INC2_different_cluster = " + json.dumps(Distribution_cluster)+ ";"
    standardization = "var Standardization = " + json.dumps(standardization)+ ";"
    Stacked_Chart = "var Stacked_Chart = " + json.dumps(Stacked_Chart)+ ";"
    Transition_Chart = "var Transition_Chart = " + json.dumps(Transition_Chart)+ ";"
    Parallel_Categories_Diagram = "var Parallel_Categories_Diagram = " + json.dumps(Parallel_Categories_Diagram)+ ";"
    Chord_Diagram = "var Chord_Diagram = " + json.dumps(Chord_Diagram)+ ";"
    HeatmapTitle = 'var HeatmapTitle = "' + str(HeatmapTitle) + '";'
    Heatmap = "var Heatmap = " + json.dumps(Heatmap)+ ";"
    Horizontal_Bar_Title = 'var Horizontal_Bar_Title = "' + str(Horizontal_Bar_Title) + '";'
    HorizonalBarChart = "var HorizonalBarChart = " + json.dumps(HorizonalBarChart)+ ";"
    Map_width = 'var Map_width  = "' + Map_width + '";'
    Map_height = 'var Map_height = "' + Map_height + '";'
    
    
    contents = contents.replace("var InitialLayers = [];", InitialLayers)
    contents = contents.replace('var SubjectName = "";', SubjectName)
    contents = contents.replace("var allMetros = false;", allMetros)
    contents = contents.replace("var Index_of_neighborhood_change = false;", Index_of_neighborhood_change)
    contents = contents.replace("var Qualitative_Maps = true;", Qualitative_Maps)
    contents = contents.replace("var Distribution_INC1 = false;", Distribution_INC1)
    contents = contents.replace("var Distribution_INC2_different_period = false;", Distribution_period)
    contents = contents.replace("var Distribution_INC2_different_cluster = false;", Distribution_cluster)
    contents = contents.replace("var Standardization = false;", standardization)
    contents = contents.replace("var Stacked_Chart = false;", Stacked_Chart)
    contents = contents.replace("var Transition_Chart = false;", Transition_Chart)
    contents = contents.replace("var Parallel_Categories_Diagram = false;", Parallel_Categories_Diagram)
    contents = contents.replace("var Chord_Diagram = false;", Chord_Diagram)
    contents = contents.replace('var HeatmapTitle = "";', HeatmapTitle)
    contents = contents.replace("var Heatmap = false;", Heatmap)
    contents = contents.replace('var Horizontal_Bar_Title = "";', Horizontal_Bar_Title)    
    contents = contents.replace("var HorizonalBarChart = false;", HorizonalBarChart)
    contents = contents.replace('var Map_width  = "400px";', Map_width)
    contents = contents.replace('var Map_height = "400px";', Map_height)
    
    
    #Write output including the replacement above
    filename_GEO_CONFIG = "NAM_" + param['filename_suffix'] + "/data/GEO_CONFIG_"+param['filename_suffix']+".js"
    ofile = open(filename_GEO_CONFIG, 'w', encoding="utf-8")
    ofile.write(contents)
    ofile.close()


def write_ALL_METROS_GEO_CONFIG_js(param):
    # read GEO_CONFIG.js
    ifile = open("template/ACM_GEO_CONFIG.js", "r", encoding="utf-8")
    contents = ifile.read()
    
    Stacked_Chart = False;
    Correlogram = False;
    Scatter_Plot = False;               
    Parallel_Coordinates_Plot = False;                  
    
    # perpare parameters
    NumOfMaps = 1
    InitialLayers = ["INC"]
    
    # Automatically set Map_width, Map_height. 
    Map_width = "1400px"
    Map_height = "800px"
    
    # replace newly computed "NumOfMaps", "InitialLayers", "Map_width", "Map_height" in CONFIG.js. See the example replacement below
    NumOfMaps = "var NumOfMaps = " + str(NumOfMaps) + ";"
    InitialLayers = "var InitialLayers = " + json.dumps(InitialLayers) + ";"
    Initial_map_center = "var Initial_map_center = [37, -98.5795];"
    Initial_map_zoom_level = "var Initial_map_zoom_level = 5;"
    Map_width = 'var Map_width  = "' + Map_width + '";'
    Map_height = 'var Map_height = "' + Map_height + '";'
    
    contents = contents.replace("var NumOfMaps = 1;", NumOfMaps)
    contents = contents.replace("var InitialLayers = [];", InitialLayers)
    contents = contents.replace("//var Initial_map_center = [34.0522, -117.9];", Initial_map_center)
    contents = contents.replace("//var Initial_map_zoom_level = 8;", Initial_map_zoom_level)
    contents = contents.replace('var Map_width  = "400px";', Map_width)
    contents = contents.replace('var Map_height = "400px";', Map_height)
    
    #Stacked_Chart = "var Stacked_Chart = false;"
    #Correlogram = "var Correlogram = false;"
    #Scatter_Plot = "var Scatter_Plot = false;"
    #Parallel_Coordinates_Plot = "var Parallel_Coordinates_Plot = false;"
    
    #contents = contents.replace("var Stacked_Chart = false;", Stacked_Chart)
    #contents = contents.replace("var Correlogram = false;", Correlogram)
    #contents = contents.replace("var Scatter_Plot = false;", Scatter_Plot)
    #contents = contents.replace("var Parallel_Coordinates_Plot = false;", Parallel_Coordinates_Plot)
    
    #Write output including the replacement above
    filename_GEO_CONFIG = "NAM_" + param['filename_suffix'] + "/data/GEO_CONFIG_"+param['filename_suffix']+".js"
    ofile = open(filename_GEO_CONFIG, 'w', encoding="utf-8")
    ofile.write(contents)
    ofile.close()


def write_GEO_JSON_js(community, param):
    # query geometry for each tract
    geoid = community.gdf.columns[0]
    tracts = community.gdf[[geoid, 'geometry']].copy()
    tracts.drop_duplicates(subset=geoid, inplace=True)					# get unique geoid
    
    # open GEO_JSON.js write heading for geojson format
    filename_GEO_JSON = "NAM_" + param['filename_suffix'] + "/data/GEO_JSON_"+param['filename_suffix']+".js"
    ofile = open(filename_GEO_JSON, 'w')
    ofile.write('var GEO_JSON =\n')
    ofile.write('{"type":"FeatureCollection", "features": [\n')
    
    #Convert geometry in GEOJSONP to geojson format
    wCount = 0
    for tract in tracts.itertuples():
        feature = {"type":"Feature"}
        if (isinstance(tract.geometry, float) and math.isnan(tract.geometry)) or tract.geometry is None:								# check is NaN?
            #print(tract.geometry)
            continue
        #print("tracts#######################################################################")
        #print(tract.geometry)
    
        feature["geometry"] = shapely.geometry.mapping(tract.geometry)
        #feature["properties"] = {geoid: tract.__getattribute__(geoid), "tractID": tract.__getattribute__(geoid)}
        feature["properties"] = {geoid: tract.__getattribute__(geoid)}
        wCount += 1
        ofile.write(json.dumps(feature)+',\n')
    #print("GEO_JSON.js write count:", wCount)
    # complete the geojosn format by adding parenthesis at the end.	
    ofile.write(']}\n')
    ofile.close()


def write_ALL_METROS_JSON_js(metros, param):
    # query geometry for each tract
    geoid = metros.columns[0]
    tracts = metros[[geoid, 'name', 'geometry']].copy()
    tracts.drop_duplicates(subset=geoid, inplace=True)					# get unique geoid
    #print(tracts)
    
    # open GEO_JSON.js write heading for geojson format
    filename_GEO_JSON = "NAM_" + param['filename_suffix'] + "/data/GEO_JSON_"+param['filename_suffix']+".js"
    ofile = open(filename_GEO_JSON, 'w')
    ofile.write('var GEO_JSON =\n')
    ofile.write('{"type":"FeatureCollection", "features": [\n')
    
    #Convert geometry in GEOJSONP to geojson format
    wCount = 0
    for tract in tracts.itertuples():
        feature = {"type":"Feature"}
        #if (type(tract.geometry) is float):								# check is NaN?
        if (isinstance(tract.geometry, float) and math.isnan(tract.geometry)) or tract.geometry is None:
            #print(tract.geometry)
            continue
        feature["geometry"] = shapely.geometry.mapping(tract.geometry)
        #feature["properties"] = {geoid: tract.__getattribute__(geoid), "tractID": tract.__getattribute__(geoid)}
        feature["properties"] = {geoid: tract.geoid, 'metro': tract.name}
        wCount += 1
        ofile.write(json.dumps(feature)+',\n')
    #print("GEO_JSON.js write count:", wCount)
    # complete the geojosn format by adding parenthesis at the end.	
    ofile.write(']}\n')
    ofile.close()


def write_GEO_VARIABLES_js(community, param):
    #print(param)
    geoid     = community.gdf.columns[0]
    method    = param['method']
    nClusters = param['nClusters']
    years     = param['years']
    variables = param['variables']
    labels    = param['labels']
    if 'standardization' in param:
        standardization = param['standardization']
    else:
        standardization = False
    
    seqClusters = 5
    distType    = 'tran'
    #if ('Sequence' in param and type(param['Sequence']) is dict and 'seq_clusters' in param['Sequence']): 
    #	seqClusters = param['Sequence']['seq_clusters']
    #if ('Sequence' in param and type(param['Sequence']) is dict and 'dist_type' in param['Sequence']): 
    #	distType = param['Sequence']['dist_type']
    
    if ('Sequence' in param and type(param['Sequence']) is dict):
        if ('seq_clusters' in param['Sequence']): seqClusters = param['Sequence']['seq_clusters']
        if ('dist_type' in param['Sequence']): distType = param['Sequence']['dist_type']
    
    # filtering by years
    community.gdf = community.gdf[community.gdf.year.isin(years)]
    communitySave = community.gdf[community.gdf.year.isin(years)].copy(deep=True)
    #selected_gdf = community.gdf[community.gdf.year.isin(years)].copy()
    #print(community.gdf)
    #community.gdf.to_csv(r'output_community_gdf.csv')
    
    # if standardization == True, we have to change input to zscore by yeas
    if standardization:
        data_cols = []                      # get column names except 'geoid', 'year', 'name', 'geometroy'
        for col in community.gdf.columns.tolist():
            if col == 'geoid': continue
            if col == 'year': break
            data_cols.append(col)
        #print("data_cols: ", data_cols)
        zdf = pd.DataFrame()                # blank data frame for append
        for year in years:
            gdf_of_the_year = community.gdf[community.gdf.year.isin([year])].copy(deep=True)           # gdf of a year
            gdf_of_the_year = gdf_of_the_year.reset_index(drop=True)
            #print(gdf_of_the_year)
            for col in data_cols:
                #if col != "% Mexican birth/ethnicity": continue
                col_ndarray = gdf_of_the_year.loc[:,col].to_numpy()
                new_ndarray = col_ndarray[~np.isnan(col_ndarray)]           # select not NaN value
                out_ndarray = stats.zscore(new_ndarray)
                if len(out_ndarray) == 1: out_ndarray[0] = 0.0
                k = 0
                for j, val in enumerate(col_ndarray):
                    if not np.isnan(val):
                        col_ndarray[j] = out_ndarray[k]
                        k += 1
                #if (len(col_ndarray) != len(out_ndarray)):
                #    #print(gdf_of_the_year.loc[:,col])
                #    #print("new_ndarray:", len(new_ndarray))
                #    #print("out_ndarray:", len(out_ndarray))
                #    #print("col_ndarray:", col_ndarray)
                #    print(year, "   nCols:", len(col_ndarray), "   nNaN:", len(col_ndarray)-len(out_ndarray), "   ", col)
                gdf_of_the_year.loc[:,col] = col_ndarray
                #sys.exit()
            zdf = pd.concat([zdf, gdf_of_the_year])
            #sys.exit()
        zdf = zdf.reset_index(drop=True)
        #print(zdf)
        community.gdf = zdf
        #print(community.gdf)
        #community.gdf.to_csv(r'output_standardization_zscore.csv')
        #sys.exit()
    #print(community.gdf)
    # clustering by method, nClusters with filtering by variables
    #clusters = geosnap.analyze.cluster(community, method=method, n_clusters=nClusters, columns=variables)
    #df = clusters.census[['year', method]]
    
    if (method == 'kmeans' or method == 'ward' or method == 'affinity_propagation' or method == 'spectral' or method == 'gaussian_mixture' or method == 'hdbscan'):
        clusters = community.cluster(columns=variables, method=method, n_clusters=nClusters)
    if (method == 'ward_spatial' or method == 'spenc' or method == 'skater' or method == 'azp' or method == 'max_p'):
        #clusters = community.cluster_spatial(columns=variables, method=method, n_clusters=nClusters)		
        clusters = community.regionalize(columns=variables, method=method, n_clusters=nClusters)		
    #print(clusters.gdf); print(clusters.gdf[['year', 'geoid', 'kmeans']])
    
    # pivot by year column and reset index
    df_pivot = clusters.gdf.reset_index().pivot(index=geoid, columns="year", values=method).reset_index()
    for year in years:                                                  # convert str to float for NaN
        df_pivot[year] = pd.to_numeric(df_pivot[year], downcast='float', errors='coerce')
    #print('\ndf_pivot: ', type(df_pivot));  print(df_pivot)
    
    # Use the sequence method to obtain the distance matrix of neighborhood sequences
    gdf_new, df_wide, seq_dis_mat = clusters.sequence(seq_clusters=seqClusters, dist_type=distType, cluster_col=method)
    
    # change the last column name of df_wide from 'tran-5' to 'Sequence'
    lastColumn = df_wide.columns[df_wide.shape[1]-1]
    df_wide.rename(columns={lastColumn: 'Sequence'}, inplace=True)
    #print('\ndf_wide: ', type(df_wide));  print(df_wide)
    
    # insert column 'Sequence' to df_pivot
    dict_Sequence = df_wide.to_dict()['Sequence']                       # {'48201100000': 1, '48201556000': 3, ... }
    #print(dict_Sequence)
    df_pivot['Sequence'] = df_pivot[geoid].map(dict_Sequence)
    #print(df_pivot)
    df_pivot = df_pivot.set_index(geoid)                                # set index
    #print('df_pivot: ', type(df_pivot));  print(df_pivot.columns);  print(df_pivot)
    #sys.exit()
    
    if (len(years) > 1):
        # convert df_pivot to list for INCS.linc
        yearList = []
        #for year in df_pivot.columns:
        for year in years:
            aYearList = df_pivot[year].values.tolist()
            aYearList = list(map(float, aYearList)) 
            yearList.append(aYearList)
        #print(yearList)
        # calculate INC
        incs = linc(yearList)
        #print(incs)
        #incs = minmax_scale(incs, feature_range=(0,1), axis=0)
        #print(incs)		
        # insert INC to first column of df_pivot
        df_pivot.insert(loc=0, column='INC', value=incs)
    
    if ('Sequence' not in param or not param['Sequence']): df_pivot.drop(columns=['Sequence'], inplace=True)
    #if ('Sequence' not in param or type(param['Sequence']) is not dict): df_pivot.drop(columns=['Sequence'], inplace=True)
    #print(df_pivot)
    
    # calculate zscore
    clusters_flattened = pd.DataFrame(df_pivot.to_records())                   # convert pivot to data frame
    #clusters_flattened.to_csv(r'output_clusters_flattened.csv')
    
    # drop the rows if Sequence is NaN
    #clusters_flattened = clusters_flattened[clusters_flattened.Sequence.notnull()].reset_index(drop=True)
    #clusters_flattened = clusters_flattened.reset_index(drop=True)
    geoids = clusters_flattened["geoid"].tolist()                              # get list of geoids from pivot
    #print('clusters_flattened: ', type(clusters_flattened));  print(clusters_flattened)
    
    lastClusterNo = 0
    for y, year in enumerate(years):
        #maxClusterNo_theYear = clusters_flattened[str(year)].max()
        maxClusterNo_theYear = clusters_flattened[str(year)].dropna().max()
        if (lastClusterNo < maxClusterNo_theYear): 
            lastClusterNo = maxClusterNo_theYear
    #print("lastClusterNo:", type(lastClusterNo), lastClusterNo)
    nGeneratedClusters = int(lastClusterNo + 1)
    zScore = [[0 for v in range(len(variables))] for c in range(nGeneratedClusters)]
    
    if standardization == False:        # old method
        # get all rows of valid geoids from community.gdf
        valid_gdf = community.gdf[community.gdf.geoid.isin(geoids)]
        #print("valid_gdf:", valid_gdf)
        zValue = [[0 for v in range(len(variables))] for c in range(nGeneratedClusters)]
        zCount = [[0 for v in range(len(variables))] for c in range(nGeneratedClusters)]
        # get sum of the each cluster and count of the each cluster
        for v, variable in enumerate(variables):
            #if (v > 0): break
            theVariable_pivot = valid_gdf.pivot(index='geoid', columns='year', values=variable)
            theVariable_flattened = pd.DataFrame(theVariable_pivot.to_records())   # convert pivot to data frame
            #print(theVariable_pivot)
            #print("theVariable_flattened: ", variable)
            #print(theVariable_flattened)
            if (theVariable_flattened.shape[0] != len(geoids)):         # check number of pivot and valid geoids
                print("Number of valid geoid not equal pivot of '" + variable +"'")
                print("Number of geoids: ", len(geoids))
                print("Number of pivot : ", theVariable_flattened.shape[0])
                continue
            
            # make a variable list of all years from pivot
            theVariableZscore = np.array([])
            for y, year in enumerate(years):
                theVariableZscore = np.append(theVariableZscore, theVariable_flattened[str(year)].tolist())
            #print("theVariableZscore: ", theVariableZscore.shape[0], theVariableZscore.tolist())
            
            notNaN_ndarray = theVariableZscore[~np.isnan(theVariableZscore)]        # select not NaN value
            notNaN_ndarray = stats.zscore(notNaN_ndarray)                           # calculate zscore
            if len(notNaN_ndarray) == 1: notNaN_ndarray[0] = 0.0
            k = 0
            for j, val in enumerate(theVariableZscore):
                if not np.isnan(val):
                    theVariableZscore[j] = notNaN_ndarray[k]
                    k += 1
            #print("theVariableZscore: ", theVariableZscore.shape[0], theVariableZscore.tolist())
            
            for y, year in enumerate(years):
                i = y * clusters_flattened.shape[0]
                for j, row in clusters_flattened.iterrows():
                    cluster = row[str(year)]
                    #print("zValue[%d][%d] += theVariableZscore[%d]" % (cluster, v, i+j))
                    if not np.isnan(cluster):
                        cluster = int(cluster)
                        zValue[cluster][v] += theVariableZscore[i+j]    # accumulate zscore to the position of cluster
                        zCount[cluster][v] += 1                         # count up by 1 to the position of cluster
                    # print information of NaN value in the result of zscore
                    #else:
                    #    print('cluster: ', cluster, '   y: ', y, '   j: ', j, '   v: ', v)
        #print("zValue: ", zValue);  print("zCount: ", zCount)            
        # calculate average of zscore
        for v, variable in enumerate(variables):
            for c in range(nGeneratedClusters):
                if (zCount[c][v] != 0): zScore[c][v] = round(zValue[c][v] / zCount[c][v], 2)
    
    if standardization == True:        # new method from 2023-09-28
        # get all rows of valid geoids from community.gdf
        valid_gdf = communitySave[communitySave.geoid.isin(geoids)]
        #print("valid_gdf:", valid_gdf)
        zValue = [[[0 for i in range(len(variables))] for y in range(len(years))] for c in range(nGeneratedClusters)]
        zCount = [[[0 for i in range(len(variables))] for y in range(len(years))] for c in range(nGeneratedClusters)]
        # get sum of the each cluster and count of the each cluster
        for v, variable in enumerate(variables):
            #if (v > 0): break
            theVariable_pivot = valid_gdf.pivot(index='geoid', columns='year', values=variable)
            theVariable_flattened = pd.DataFrame(theVariable_pivot.to_records())   # convert pivot to data frame
            #print(theVariable_pivot)
            #print("theVariable_flattened: ", variable)
            #print(theVariable_flattened)
            if (theVariable_flattened.shape[0] != len(geoids)):         # check number of pivot and valid geoids
                print("Number of valid geoid not equal pivot of '" + variable +"'")
                print("Number of geoids: ", len(geoids))
                print("Number of pivot : ", theVariable_flattened.shape[0])
                continue
            
            # make a variable list of all years from pivot
            theVariableZscore = np.empty([len(years), theVariable_flattened.shape[0]])
            for y, year in enumerate(years):
                theVariableZscore[y] = np.array(theVariable_flattened[str(year)].tolist())
                
                notNaN_ndarray = theVariableZscore[y][~np.isnan(theVariableZscore[y])]  # select not NaN value
                notNaN_ndarray = stats.zscore(notNaN_ndarray)                           # calculate zscore
                if len(notNaN_ndarray) == 1: notNaN_ndarray[0] = 0.0
                k = 0
                for j, val in enumerate(theVariableZscore[y]):
                    if not np.isnan(val):
                        theVariableZscore[y, j] = notNaN_ndarray[k]
                        k += 1
                #print("theVariableZscore[{}]: ".format(y), theVariableZscore[y].shape[0], theVariableZscore[y][:5])
                
            for y, year in enumerate(years):
                #i = y * clusters_flattened.shape[0]
                for j, row in clusters_flattened.iterrows():
                    cluster = row[str(year)]
                    if not np.isnan(cluster):
                        cluster = int(cluster)
                        zValue[cluster][y][v] += theVariableZscore[y, j]    # accumulate zscore to the position of cluster
                        zCount[cluster][y][v] += 1                          # count up by 1 to the position of cluster
                    # print information of NaN value in the result of zscore
                    #else:
                    #    print('cluster: ', cluster, '   y: ', y, '   j: ', j, '   v: ', v)
                    
        # calculate average of zscore
        for v, variable in enumerate(variables):
            for c in range(nGeneratedClusters):
                tScore = 0.0
                for y in range(len(years)):
                    if (zCount[c][y][v] != 0): score = zValue[c][y][v] / zCount[c][y][v]
                    tScore += score
                if (len(years) != 0): zScore[c][v] = round(tScore / len(years), 2)
    #to_csv_write("zValue", standardization, nClusters, years, variables, zValue)
    #to_csv_write("zCount", standardization, nClusters, years, variables, zCount)
    #to_csv_write("zScore", standardization, nClusters, years, variables, zScore)
    #print("\nzValue:", zValue)
    #print("\nzCount:", zCount)
    #print("\nzScore:", zScore)
    #sys.exit()
    
    # write df_pivot to GEO_VARIABLES.js
    filename_GEO_VARIABLES = "NAM_" + param['filename_suffix'] + "/data/GEO_VARIABLES_"+param['filename_suffix']+".js"
    ofile = open(filename_GEO_VARIABLES, 'w')
    ofile.write('var GEO_VARIABLES =\n')
    ofile.write('[\n')
    #heading = [geoid, 'INC']
    #if (len(years) <= 1): heading = [geoid]
    #heading.extend(list(map(str, years)))
    heading = [geoid]
    heading.extend(list(map(str, df_pivot.columns.tolist())))
    ofile.write('  '+json.dumps(heading)+',\n')
    wCount = 0
    for i, row in df_pivot.reset_index().iterrows():
        aLine = row.tolist()
        for j, col in enumerate(aLine[2:], 2):
            try:
                aLine[j] = int(col)                                  # convert float to int
            except ValueError:
                aLine[j] = -9999                                     # if Nan, set -9999
        wCount += 1 
        ofile.write('  '+json.dumps(aLine)+',\n')
    #print("GEO_VARIABLES.js write count:", wCount)
    ofile.write(']\n')
    
    # write zscore to GEO_VARIABLES.js
    ofile.write('\n')
    ofile.write('var GEO_ZSCORES =\n')
    ofile.write('{\n')
    ofile.write('  "xAxis": [\n')
    for v, variable in enumerate(labels):
        ofile.write('    "'+variable+'",\n')
    ofile.write('  ],\n')
    ofile.write('  "yAxis": '+json.dumps(["T"+str(c) for c in range(nGeneratedClusters)])+',\n')
    ofile.write('  "data" : [\n')
    for z, row in enumerate(zScore):
        ofile.write('    '+json.dumps(row)+',\n')
    ofile.write('  ],\n')
    ofile.write('}\n')
    
    ofile.close()

'''
def write_ALL_METROS_VARIABLES_js(metros, param):
    geoid       = metros.columns[0]
    method      = param['method']
    nClusters   = param['nClusters']
    years       = param['years']
    variables   = param['variables']
    seqClusters = 5
    distType    = 'tran'
    
    if ('Sequence' in param and type(param['Sequence']) is dict):
        if ('seq_clusters' in param['Sequence']): seqClusters = param['Sequence']['seq_clusters']
        if ('dist_type' in param['Sequence']): distType = param['Sequence']['dist_type']
    
    #msas = data_store.msa_definitions
    #for column in msas.columns:
    #	print(column)
    #print(msas)
    
    #community = Community.from_ltdb(years=years, msa_fips="10220")
    #community = Community.from_ltdb(years=years)
    #community.gdf = community.gdf[['geoid', 'year']]
    #print(community.gdf)
    #print(variables)
    #print(variables.append(['geoid', 'year']))
    #print(variables)
    #return
    
    # Initial call to print 0% progress
    printProgressBar(0, len(metros.index), prefix = 'Progress:', suffix = 'Complete', length = 50)
    
    readCount = 0
    outList = []
    for index, metro in metros.iterrows():
        #if (index > 10): break
        #if (index != 3): continue
        #print(index, metro['geoid'], metro['name'])
        metroid = metro['geoid']
        p = metro['name'].rfind(', ')
        #if (p < 0): print(index, metro['geoid'], metro['name'], p)
        metroname = metro['name'][:p]
        stateabbr = metro['name'][p+2:]
        #print(index, metroid, stateabbr, metroname)
        
        try:
            community = Community.from_ltdb(years=years, msa_fips=metroid)
        except ValueError:
            continue
        #printProgressBar(index, len(metros.index), prefix = 'Progress:', suffix = 'Complete', length = 50)
        #continue
        
        if (len(community.gdf.index) <= 0): continue
        #print(community.gdf.columns)
        #for column in community.gdf.columns:
        #	print(column)
        #print(community)
        #print(community.gdf)
        
        # clustering by method, nClusters with filtering by variables
        try:
            clusters = community.cluster(columns=variables, method=method, n_clusters=nClusters)
        except KeyError:
            continue
        #print(clusters.gdf)
        #print(clusters.gdf[['year', 'geoid', 'kmeans']])
        
        # get pivot from clusters
        df_pivot = clusters.gdf.pivot(index='geoid', columns='year', values='kmeans')
        #print(df_pivot)
        #print(len(df_pivot.index))
        #print(df_pivot.columns)
        
        if (len(df_pivot.columns) > 1):										# 1980, 1990, 2000, 2010
            # convert df_pivot to list for INCS.linc
            yearList = []
            for year in df_pivot.columns:
                aYearList = df_pivot[year].values.tolist()
                aYearList = list(map(float, aYearList)) 
                yearList.append(aYearList)
            #print(yearList)
            # calculate INC
            incs = linc(yearList)
            #print(incs)
            ave = sum(incs) / len(incs) if (len(incs) != 0) else -9999
            #print("ave:", ave)
            #print(index, metroid, ave, stateabbr, metroname)
            readCount += len(incs)
            outList.append([metroid, ave])
            printProgressBar(index, len(metros.index), prefix = 'Progress:', suffix = 'Complete', length = 50)
    printProgressBar(len(metros.index), len(metros.index), prefix = 'Progress:', suffix = 'Complete', length = 50)
    #print(outList)
    print("readCount:", readCount)
    
    # write df_pivot to GEO_VARIABLES.js
    filename_GEO_VARIABLES = "NAM_" + param['filename_suffix'] + "/data/GEO_VARIABLES_"+param['filename_suffix']+".js"
    ofile = open(filename_GEO_VARIABLES, 'w')
    ofile.write('var GEO_VARIABLES =\n')
    ofile.write('[\n')
    heading = [geoid, 'INC']
    ofile.write('  '+json.dumps(heading)+',\n')
    wCount = 0
    for i, row in enumerate(outList):
        wCount += 1
        ofile.write('  '+json.dumps(row)+',\n')
    #print("GEO_VARIABLES.js write count:", wCount)
    ofile.write(']\n')
    ofile.close()
'''

def write_ALL_METROS_VARIABLES_js(metros, param):
    geoid       = metros.columns[0]
    method      = param['method']
    nClusters   = param['nClusters']
    years       = param['years']
    variables   = param['variables']
    seqClusters = 5
    distType    = 'tran'
    
    if ('Sequence' in param and type(param['Sequence']) is dict):
        if ('seq_clusters' in param['Sequence']): seqClusters = param['Sequence']['seq_clusters']
        if ('dist_type' in param['Sequence']): distType = param['Sequence']['dist_type']
    
    printProgressBar(-1, len(metros.index), prefix = 'Progress:', suffix = 'Initializing', length = 50)
    
    states = datasets.states()								# [56 rows x 3 columns]
    #print(states)
    #print(states["geoid"].tolist())
    
    counties = datasets.counties()							# [3233 rows x 2 columns]
    #print(counties)
    
    ltdb = datasets.ltdb													# [330388 rows x 192 columns]
    #for column in ltdb.columns:
    #	print(column)
    #print(ltdb.memory_usage(index=True, deep=True).sum())
    #print(ltdb)
    
    msas = datasets.msa_definitions()										# [1915 rows x 13 columns]
    #for column in msas.columns:
    #	print(column)
    msas.set_index('stcofips', inplace=True)
    #print(msas)
    #print(msas.loc['48505', 'CBSA Code'])
    
    community = Community.from_ltdb(years=years, state_fips=states["geoid"].tolist())
    #community = Community.from_ltdb(state_fips=states["geoid"].tolist())	# [330388 rows x 194 columns]
    #community = Community.from_ltdb(years=years)
    #community.gdf = community.gdf[['geoid', 'year']]
    #for column in community.gdf.columns:
    #	print(column)
    
    #community.gdf['metroid'] = None
    metroids = []
    for index, row in community.gdf.iterrows():
        stcofips = row['geoid'][:5]
        try:
            metroids.append(msas.loc[stcofips, 'CBSA Code'])
        except KeyError:
            metroids.append(None)
    community.gdf.insert(0, "stcofips", metroids, True)
    #print(community.gdf.memory_usage(index=True, deep=True).sum())
    #print(community.gdf)
    #print(variables)
    #print(['geoid', 'year'] + variables)
    #print(variables)
    
    allgdf = community.gdf[['stcofips', 'geoid', 'year', 'geometry'] + variables].copy()
    allgdf.set_index('stcofips', inplace=True)
    #print(allgdf.memory_usage(index=True, deep=True).sum())
    #print(allgdf)
    
    #community.gdf = allgdf.loc['10220']
    #clusters = community.cluster(columns=variables, method=method, n_clusters=nClusters)
    #print(clusters.gdf)
    
    # Initial call to print 0% progress
    printProgressBar(0, len(metros.index), prefix = 'Progress:', suffix = 'Complete      ', length = 50)
    
    readCount = 0
    outList = []
    for index, metro in metros.iterrows():
        #if (index > 10): break
        #if (index != 3): continue
        #print(index, metro['geoid'], metro['name'])
        metroid = metro['geoid']
        p = metro['name'].rfind(', ')
        #if (p < 0): print(index, metro['geoid'], metro['name'], p)
        metroname = metro['name'][:p]
        stateabbr = metro['name'][p+2:]
        #print(index, metroid, stateabbr, metroname)
        
        #msa_fips = metroid
        #fips_list = []
        #if msa_fips:
        #	fips_list += data_store.msa_definitions[
        #		data_store.msa_definitions["CBSA Code"] == msa_fips
        #	]["stcofips"].tolist()
        ##print(metroid, fips_list)
        #
        #dfs = []
        #for fips_code in fips_list:
        #	#dfs.append(data[data.geoid.str.startswith(index)])
        #	dfs.append(allgdf[allgdf.geoid.str.startswith(fips_code)])
        #if (len(dfs) == 0): continue
        ##print(type(dfs))
        ##print(dfs)
        
        try:
            #community = Community.from_ltdb(years=years, msa_fips=metroid)
            community.gdf = allgdf.loc[metroid]
            #community.gdf = allgdf.loc[allgdf['stcofips']==metroid]
            #community.gdf = pd.concat(dfs)
            #print(community.gdf)
        #except ValueError:
        except KeyError:
            continue
        #printProgressBar(index, len(metros.index), prefix = 'Progress:', suffix = 'Complete', length = 50)
        #continue
        
        if (len(community.gdf.index) <= 0): continue
        #print(community.gdf.columns)
        #for column in community.gdf.columns:
        #	print(column)
        #print(community)
        #community.gdf.to_csv(r'output.csv')
        #print(community.gdf)
        #print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")		
        # clustering by method, nClusters with filtering by variables
        #try:
        if (method == 'kmeans' or method == 'ward' or method == 'affinity_propagation' or method == 'spectral' or method == 'gaussian_mixture' or method == 'hdbscan'):
            try:
                clusters = community.cluster(columns=variables, method=method, n_clusters=nClusters)
            except KeyError:
                continue
                
        if (method == 'ward_spatial' or method == 'spenc' or method == 'skater' or method == 'azp' or method == 'max_p'):
            try:
                #clusters = community.cluster_spatial(columns=variables, method=method, n_clusters=nClusters) #, spatial_weights='rook'
                clusters = community.regionalize(columns=variables, method=method, n_clusters=nClusters) #, spatial_weights='rook'
            except KeyError:
                continue
        #except KeyError:
        #	continue
        #print(clusters.gdf)
        #print(clusters.gdf[['year', 'geoid', 'kmeans']])
        
        # get pivot from clusters
        df_pivot = clusters.gdf.pivot(index='geoid', columns='year', values='kmeans')
        #print(df_pivot)
        #print(len(df_pivot.index))
        #print(df_pivot.columns)
        
        if (len(df_pivot.columns) > 1):										# 1980, 1990, 2000, 2010
            # convert df_pivot to list for INCS.linc
            yearList = []
            for year in df_pivot.columns:
                aYearList = df_pivot[year].values.tolist()
                aYearList = list(map(float, aYearList)) 
                yearList.append(aYearList)
            #print(yearList)
            # calculate INC
            incs = linc(yearList)
            #print(incs)
            ave = sum(incs) / len(incs) if (len(incs) != 0) else -9999
            #print("ave:", ave)
            #print(index, metroid, ave, stateabbr, metroname)
            readCount += len(incs)
            outList.append([metroid, ave])
            printProgressBar(index, len(metros.index), prefix = 'Progress:', suffix = 'Complete', length = 50)
    printProgressBar(len(metros.index), len(metros.index), prefix = 'Progress:', suffix = 'Complete', length = 50)
    #print(outList)
    #print("readCount2:", readCount)
    
    # write df_pivot to GEO_VARIABLES.js
    filename_GEO_VARIABLES = "NAM_" + param['filename_suffix'] + "/data/GEO_VARIABLES_"+param['filename_suffix']+".js"
    ofile = open(filename_GEO_VARIABLES, 'w')
    ofile.write('var GEO_VARIABLES =\n')
    ofile.write('[\n')
    heading = [geoid, 'INC']
    ofile.write('  '+json.dumps(heading)+',\n')
    wCount = 0
    for i, row in enumerate(outList):
        wCount += 1
        ofile.write('  '+json.dumps(row)+',\n')
    #print("GEO_VARIABLES.js write count:", wCount)
    ofile.write(']\n')
    ofile.close()


def Clustering_viz(param):
    write_LOG(param)
    
    # select community by state_fips, msa_fips, county_fips
    metros = None
    community = None
    if ('allMetros' in param and param['allMetros']):
        #metros = data_store.msa_definitions
        #print("metros: " + metros)
        #metros = data_store.msas()
        metros = datasets.msas()
        print("##################################################### metros")
        print(metros)
    elif ('msa_fips' in param and param['msa_fips']):
        community = Community.from_ltdb(years=param['years'], msa_fips=param['msa_fips'])
        #community = Community.from_ltdb(msa_fips=param['msa_fips'])
    elif ('county_fips' in param and param['county_fips']):
        community = Community.from_ltdb(years=param['years'], county_fips=param['county_fips'])
    elif ('state_fips' in param and param['state_fips']):
        community = Community.from_ltdb(years=param['years'], state_fips=param['state_fips'])
    
    ################################################################################################################    
    
    
    # This is executed when the user enter attributes in csv file and geometroy in shapefile ######################  
    if (community is None and 'inputCSV' in param and param['inputCSV']):
        community = Community()
        #"""
        attr_df = pd.read_csv(param['inputCSV'])
        attr_df["geoid"] = attr_df["geoid"].astype(str)
        boundary_df = gpd.read_file(param['shapefile'])
        boundary_df = boundary_df.rename(columns={"GEOID10":"geoid"})
        boundary_df["geoid"] = boundary_df["geoid"].astype(str)
        joined_df = attr_df.merge(boundary_df,on="geoid", how="left")
        joined_df = joined_df.dropna(subset=["geometry"])
        community.gdf = joined_df
        """
        #community.gdf = param['inputCSV']
        community.gdf = pd.read_csv(param['inputCSV'], dtype={'geoid':str})
        geoid = community.gdf.columns[0]
        #community.gdf = community.gdf.astype(str)
        #print("inputCSV:  " + community.gdf.geoid)		
        community.gdf['geoid'] = community.gdf['geoid'].astype(str)
        #print("community.gdf.columns[0]:", community.gdf.columns[0])
        
        # read shape file to df_shape
        df_shape = gpd.read_file(param['shapefile'])
        df_shape = df_shape.astype(str)	 
        #print("shapefile:  " + df_shape.GEOID10)		
        df_shape = df_shape.set_index("GEOID10")
        
        # insert geometry to community.gdf
        geometry = []
        for index, row in community.gdf.iterrows():
            tractid = row[geoid]
            try:
                tract = df_shape.loc[tractid]
                geometry.append(shapely.wkt.loads(tract.geometry))
            except KeyError:
                #print("Tract ID [{}] is not found in the shape file {}".format(tractid, param['shapefile']))
                geometry.append(None)
        community.gdf.insert(len(community.gdf.columns), "geometry", geometry)
        #"""
    ################################################################################################################    
    
    #print("community.gdf: " + community.gdf)
    if community is not None:
        community.gdf = community.gdf.replace(np.inf,np.nan)
    #community.gdf = community.gdf.replace([np.inf, -np.inf], np.nan)
    codebook = pd.read_csv('template/conversion_table_codebook.csv')
    codebook.set_index(keys='variable', inplace=True)
    labels = copy.deepcopy(param['variables'])
    label = 'short_name'                                             # default
    if ('label' in param and param['label'] == 'variable'): label = 'variable'
    if ('label' in param and param['label'] == 'full_name'): label = 'full_name'
    if ('label' in param and param['label'] == 'short_name'): label = 'short_name'
    if (label != 'variable'):
        for idx, variable in enumerate(param['variables']):
            try:
                codeRec = codebook.loc[variable]
                labels[idx] = codeRec[label]
            except:
                print("variable not found in codebook.  variable:", variable)
    param['labels'] = labels
    
    #write_INDEX_html(param)
    #write_GEO_CONFIG_js(param)
    #if (community): write_GEO_VARIABLES_js(community, param)
    #if (community): write_GEO_JSON_js(community, param)
    #if (metros is not None): write_ALL_METROS_VARIABLES_js(metros, param)
    #if (metros is not None): write_ALL_METROS_JSON_js(metros, param)
    
    if (community):
        write_INDEX_html(param)
        write_GEO_CONFIG_js(param)
        write_GEO_VARIABLES_js(community, param)
        write_GEO_JSON_js(community, param)
    
    if (metros is not None):
        write_ALL_METROS_INDEX_html(param)
        write_ALL_METROS_GEO_CONFIG_js(param)
        write_ALL_METROS_VARIABLES_js(metros, param)
        write_ALL_METROS_JSON_js(metros, param)
    
    Directory_vis(param) 


def Clustering_log():
    # build array of logs from directory of 'NAM_'
    logs = []
    dirname = os.getcwd()
    subnames = os.listdir(dirname)
    for subname in subnames:
        fullpath = os.path.join(dirname, subname)
        if (not os.path.isdir(fullpath)): continue
        if (not subname.startswith('NAM_')): continue
        #print(os.path.join(fullpath, 'index.html'))
        indexfile = os.path.join(fullpath, 'index.html')
        logfile = os.path.join(fullpath, 'data/param.log')
        if (not os.path.exists(indexfile)): continue
        if (not os.path.exists(logfile)): continue
        #print(fullpath, logfile)
        # read param.log
        ifile = open(logfile, "r", encoding="utf-8")
        wholetext = ifile.read()
        contents = wholetext.split('\n', maxsplit=1)
        if (len(contents) != 2): continue
        create_at = contents[0]
        param     = contents[1]
        #print(create_at)
        #print(param)
        logs.append({'indexfile': os.path.join(subname, 'index.html'), 'create_at': create_at, 'param': param})
    logs = sorted(logs, key=lambda k: k['create_at']) 
    #print(logs)
    
    #Write output to log.html
    filename_LOG = "log.html"
    ofile = open(filename_LOG, 'w')
    ofile.write('<!DOCTYPE html>\n')
    ofile.write('<html>\n')
    ofile.write('<head>\n')
    ofile.write('  <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>\n')
    ofile.write('  <title>Neighborhood Analysis Logging</title>\n')
    ofile.write('</head>\n')
    ofile.write('<body>\n')
    ofile.write('  <header>\n')
    ofile.write('    <h1>Neighborhood Analysis Logging</h1>\n')
    ofile.write('  </header>\n')
    
    for idx, val in enumerate(logs):
        params = val['param'].split('\n')
        html = '\n'
        html += '<div style="margin:10px; float:left; border: 1px solid #99CCFF; border-radius: 5px;">\n'
        html += '  <table>\n'
        html += '    <tr>\n'
        html += '      <td>\n'
        html += '        <button id="global_submit" type="button" style="margin:0px 20px 0px 5px;" onclick="window.open(\'' + val['indexfile'] + '\')">' + str(idx+1) + '. Show This</button>\n'
        html += '        ' + val['create_at'] + '\n'
        html += '      </td>\n'
        html += '    </tr>\n'
        html += '    <tr>\n'
        html += '      <td>\n'
        html += '<pre>\n'
        for param in params:
            html += param + '\n'
        html += '</pre>\n'
        html += '      </td>\n'
        html += '    </tr>\n'
        html += '  </table>\n'
        html += '</div>\n'
        ofile.write(html)
    
    ofile.write('</body>\n')
    ofile.write('</html>')
    ofile.close()
    
    local_dir = os.path.dirname(os.path.realpath(__file__))
    fname =urllib.parse.quote(filename_LOG)
    url = 'file:' + os.path.join(local_dir, fname)
    webbrowser.open(url)


if __name__ == '__main__':
    started_datetime = datetime.now()
    dateYYMMDD = started_datetime.strftime('%Y%m%d')
    timeHHMMSS = started_datetime.strftime('%H%M%S')
    print('GEOSNAP2NAM start at %s %s' % (started_datetime.strftime('%Y-%m-%d'), started_datetime.strftime('%H:%M:%S')))
    
    #sample = "downloads/LTDB_Std_All_Sample.zip"
    #full = "downloads/LTDB_Std_All_fullcount.zip"
    #store_ltdb(sample=sample, fullcount=full)
    #store_census()
    
    param1 = {
        'title': "Neighborhood Analysis: Kmeans, 1980~2010, 5 variables",
        'filename_suffix': "All",
        'allMetros': True,
        'years': [1980, 1990, 2000, 2010],
        'method': "kmeans",
        'nClusters': 8,
        'variables': [
                    "p_nonhisp_white_persons", 
                    "p_nonhisp_black_persons", 
                    "p_hispanic_persons", 
                    "p_native_persons", 
                    "p_asian_persons",
                    ],
    }
    
    param2 = {
        'title': "Neighborhood Analysis: kmeans, IL",
        'filename_suffix': "Illinois_kmeans_Cluster6",				 # "Albertville"
        #'filename_suffix': "Albertville",				 # "Albertville"
        #'database': "ltdb",
        'state_fips': "17",
        #'msa_fips': "16980",						 # "10700" LA:31080 SD:41740
        #'msa_fips': "10700",						 # "10700"
        #'county_fips': "06037",                         # LA county: 06037, LA Orange county: 06059,  Chicago:1701
        'years': [2010],           # Available years: 1970, 1980, 1990, 2000 and 2010
        'method': "kmeans",   # Aspatial Clustering: affinity_propagation, gaussian_mixture, hdbscan, kmeans, spectral, ward
                                # Spatial Clustering: azp, max_p, skater, spenc, ward_spatial   
        'nClusters': 6,                              # This option should be commented out for affinity_propagation and hdbscan
        'variables': [
            "p_nonhisp_white_persons",
            "p_nonhisp_black_persons",
            "p_hispanic_persons",
            "p_asian_persons",
            "p_foreign_born_pop",
            "p_edu_college_greater",
            "p_unemployment_rate",
            #"p_employed_professional",
            "p_employed_manufacturing",
            "p_poverty_rate",
            "p_vacant_housing_units",
            "p_owner_occupied_units",
            "p_housing_units_multiunit_structures",
            "median_home_value",
            "p_structures_30_old",
            "p_household_recent_move",
            "p_persons_under_18",
            "p_persons_over_60",
                    ],
        #'Sequence': True,
        #'seq_clusters': 5,
        #'dist_type': 'tran',						 # hamming, arbitrary
        #'Sequence': {'seq_clusters': 2, 'dist_type': 'tran'},
        #'Sequence': False,
        # optional visualization below.
        'Index_of_neighborhood_change': True,        #choropleth map: Maps representing index of neighborhood Change
        'Qualitative_Maps': True,                #choropleth map: Maps representing clustering result		
        'Distribution_INC1': True,                   #density chart: INC changes as the map extent changes 
        #'Distribution_INC2_different_period': True,  #density chart: INC changes by different years
        #'Distribution_INC2_different_cluster': True, #density chart: INC changes by different clusters
        'Stacked_Chart': True,    #stacked chart: Temporal Change in Neighborhoods over years		
        'Parallel_Categories_Diagram': True,
        'Chord_Diagram': True,
        'Heatmap': True,
        'HorizonalBarChart': True, 
    }
    
    param3 = {
        'title': "Neighborhood Analysis: kmeans, San Diego",
        'filename_suffix': "SD_1_neighborhood", 				 # "Albertville"
        #'filename_suffix': "Albertville",				 # "Albertville"
        #'database': "ltdb",
        #'state_fips': "17",
        'msa_fips': "41740",						 # "10700" LA:31080 SD:41740
        #'msa_fips': "10700",						 # "10700"
        #'county_fips': "06037",                         # LA county: 06037, LA Orange county: 06059,  Chicago:1701
        'years': [1980, 1990, 2000, 2010],           # Available years: 1970, 1980, 1990, 2000 and 2010
        'method': "kmeans",   # Aspatial Clustering: affinity_propagation, gaussian_mixture, hdbscan, kmeans, spectral, ward
                                # Spatial Clustering: azp, max_p, skater, spenc, ward_spatial   
        'nClusters': 6,                              # This option should be commented out for affinity_propagation and hdbscan
        'variables': [
            "p_nonhisp_white_persons",
            "p_nonhisp_black_persons",
            "p_hispanic_persons",
            "p_asian_persons",
            "p_foreign_born_pop",
            "p_edu_college_greater",
            "p_unemployment_rate",
            #"p_employed_professional",
            "p_employed_manufacturing",
            "p_poverty_rate",
            "p_vacant_housing_units",
            "p_owner_occupied_units",
            "p_housing_units_multiunit_structures",
            "median_home_value",
            "p_structures_30_old",
            "p_household_recent_move",
            "p_persons_under_18",
            "p_persons_over_60",
                    ],
                        # hamming, arbitrary
        'Sequence': {'seq_clusters': 2, 'dist_type': 'tran'},
        # optional visualization below.
        'Index_of_neighborhood_change': True,        #choropleth map: Maps representing index of neighborhood Change
        'Qualitative_Maps': True,                #choropleth map: Maps representing clustering result		
        'Distribution_INC1': True,                   #density chart: INC changes as the map extent changes 
        #'Distribution_INC2_different_period': True,  #density chart: INC changes by different years
        #'Distribution_INC2_different_cluster': True, #density chart: INC changes by different clusters
        'Stacked_Chart': True,    #stacked chart: Temporal Change in Neighborhoods over years		
        'Parallel_Categories_Diagram': True,
        'Chord_Diagram': True,
        'Heatmap': True,
        'HorizonalBarChart': True, 
    }

    param = {
        'title': "Longitudinal Neighborhood Change, Cook County (tract level)",
        'subject': "NEIGHBORHOOD",
        'filename_suffix': "test",		   
        'inputCSV': "attributes/LTDB_2018_1990_2000_2010__tract_Cook_byTract_normalized.csv",   
        'shapefile': "shp/Cook_County_Tract.shp", 
        'years': [1980, 1990, 2000, 2010],		   # Available years: 1970, 1980, 1990, 2000 and 2010
        'method': "kmeans",						  # Aspatial Clustering: affinity_propagation, gaussian_mixture, hdbscan, kmeans, spectral, ward
                                                    # Spatial Clustering: azp, max_p, skater, spenc, ward_spatial   
        'nClusters': 6,							  # This option should be commented out for affinity_propagation, hdbscan and max_p 
        'variables': [
                "p_nonhisp_white_persons",
                "p_nonhisp_black_persons",
                "p_hispanic_persons",
                "p_asian_persons",
                "p_foreign_born_pop",
                "p_edu_college_greater",
                "p_unemployment_rate",
                "p_employed_manufacturing",
                "p_poverty_rate",
                "p_vacant_housing_units",
                "p_owner_occupied_units",
                "p_housing_units_multiunit_structures",
                "median_home_value",
                "p_structures_30_old",
                "p_household_recent_move",
                "p_persons_under_18",
                "p_persons_over_60",	   
                    ],
        'Sequence': {'seq_clusters': 5, 'dist_type': 'tran'},
        'Qualitative_Maps': True,				#choropleth map: Maps representing clustering result		
        'Stacked_Chart': True,	#stacked chart: Temporal Change in Neighborhoods over years		
        'Parallel_Categories_Diagram': True,
        'Chord_Diagram': True
    }
    
    paramLTDB = {
        'title': "Longitudinal Neighborhood Change, Cook County (tract level)",
        'subject': "NEIGHBORHOOD",
        'filename_suffix': "test_Cook",		   
        'inputCSV': "attributes/LTDB_2018_1990_2000_2010__tract_Cook_byTract_normalized.csv",   
        'shapefile': "shp/Cook_County_Tract.shp", 
        'years': [1980, 1990, 2000, 2010],		   # Available years: 1970, 1980, 1990, 2000 and 2010
        'method': "kmeans",						  # Aspatial Clustering: affinity_propagation, gaussian_mixture, hdbscan, kmeans, spectral, ward
                                                    # Spatial Clustering: azp, max_p, skater, spenc, ward_spatial   
        'nClusters': 6,							  # This option should be commented out for affinity_propagation, hdbscan and max_p 
        'variables': [
                "% white, non-Hispanic",
                "% black, non-Hispanic",
                "% Hispanic",
                "% Asian and Pacific Islander race",
                "% foreign born",
                "% with 4-year college degree or more",
                "p_unemployment_rate",
                "% unemployed",
                "% in poverty, total",
                "% vacant units",
                "% owner-occupied units",
                "p_housing_units_multiunit_structures",
                "% multi-family units",
                "% structures more than 30 years old",
                "% HH in neighborhood 10 years or less",
                "% 17 and under, total",
                "% 60 and older, total",	   
                    ],
        'Sequence': {'seq_clusters': 5, 'dist_type': 'tran'},
        'Qualitative_Maps': True,				#choropleth map: Maps representing clustering result		
        'Stacked_Chart': True,	#stacked chart: Temporal Change in Neighborhoods over years		
        'Parallel_Categories_Diagram': True,
        'Chord_Diagram': True
    }
# LA 31080, San Diego 41740, Albertville 10700, NY 35620
    param_Austin = {
        'title': "Longitudinal Neighborhood Change, Austin (tract level)",
        'SubjectName': "NEIGHBORHOOD",
        'filename_suffix': "LTDB_1970~2019_Austin_12420",		   
        'inputCSV': "attributes/LTDB_1970~2019_Austin_12420.csv",   
        'shapefile': "shp/Austin.shp", 
        #'shapefile': "shp/Austin.shp",     
        'years': [1990, 2000, 2010, 2019],		   # Available years: 1970, 1980, 1990, 2000, 2010, 2012, 2019
        'method': "kmeans",						  # Aspatial Clustering: affinity_propagation, gaussian_mixture, hdbscan, kmeans, spectral, ward
                                                    # Spatial Clustering: azp, max_p, skater, spenc, ward_spatial   
        'nClusters': 6,							  # This option should be commented out for affinity_propagation, hdbscan and max_p 
        'Sequence': {'seq_clusters': 5, 'dist_type': 'tran'},
        'variables': [
                "% white, non-Hispanic",   
                "% Hispanic",
                "% Asian and Pacific Islander race",
                "% foreign born",
                "% with 4-year college degree or more",
                "% unemployed",
                "% manufacturing employees",
                "% in poverty, total",
                "% vacant units",
                "% owner-occupied units",
                "% multi-family units",
                "Median home value",
                "% structures more than 30 years old",
                "% HH in neighborhood 10 years or less",
                "% 17 and under, total",
                "% 60 and older, total",   
                    ],
        # optional visualization below.
        'Index_of_neighborhood_change': True,        #choropleth map: Maps representing index of neighborhood Change
        'Qualitative_Maps': True,                    #choropleth map: Maps representing clustering result		
        'Distribution_INC1': True,                   #density chart: INC changes as the map extent changes 
        'Distribution_INC2_different_period': True,  #density chart: INC changes by different years
        'Distribution_INC2_different_cluster': True, #density chart: INC changes by different clusters
        'Stacked_Chart': True,    #stacked chart: Temporal Change in Neighborhoods over years		
        'Parallel_Categories_Diagram': True,
        'Chord_Diagram': True, 
        'HeatmapTitle': "Z Score Means across Different Neighborhood Types",
        'Heatmap': True,
        'Horizontal_Bar_Title': "Z Score Means in Different Neighborhood Types",
        'HorizonalBarChart': True,  
    }
    #Clustering_viz(param_Austin)
    
    param_Harris = {
    'title': "Longitudinal Neighborhood Change at Census Tracel Level, Harris County Houston, TX",
    'SubjectName': "NEIGHBORHOOD",
    'filename_suffix': "Houston_1970-2019",
    #'inputCSV': "attributes/LTDB_1970~2019_Houston_26420.csv",
    'inputCSV': "attributes/LTDB_1970~2019_Houston_26420_nan.csv",
    'standardization': True,
    'shapefile': "shp/Harris_county.shp", 
    'years': [1980, 1990, 2000, 2010, 2019],		   # Available years: 1970, 1980, 1990, 2000, 2010, 2012, 2019
    #'method': "kmeans_smart",
    'method': "kmeans",						  # Aspatial Clustering: affinity_propagation, gaussian_mixture, hdbscan, kmeans, spectral, ward
                                                # Spatial Clustering: azp, max_p, skater, spenc, ward_spatial   
    'nClusters': 5,							  # This option should be commented out for affinity_propagation, hdbscan and max_p 
    'Sequence': {'seq_clusters': 6, 'dist_type': 'tran'},  # tran hamming arbitrary
    'variables': [
        "Median home value",
        "% in poverty, total",
        "% unemployed",       
        "% with 4-year college degree or more",  
        "% manufacturing employees",
        "% structures more than 30 years old",
        "% HH in neighborhood 10 years or less", 
        "% owner-occupied units",
        "% multi-family units",
        "% vacant units",
        "% 60 and older, total",
        "% 17 and under, total",        
        "% white, non-Hispanic",
        "% black, non-Hispanic",         
        "% Hispanic", #
        "% Asian and Pacific Islander race", #
        "% foreign born", #
                ],
    # optional visualization below.
    'Index_of_neighborhood_change': True,        #choropleth map: Maps representing index of neighborhood Change
    'Qualitative_Maps': True,                    #choropleth map: Maps representing clustering result		
    'Distribution_INC1': False,                   #density chart: INC changes as the map extent changes 
    'Distribution_INC2_different_period': False,  #density chart: INC changes by different years
    'Distribution_INC2_different_cluster': False, #density chart: INC changes by different clusters
    'Stacked_Chart': True,    #stacked chart: Temporal Change in Neighborhoods over years		
    'Transition_Chart': True, 
    'Parallel_Categories_Diagram': True,
    'Chord_Diagram': True, 
    'HeatmapTitle': "Z Score Means across Different Neighborhood Types",
    'Heatmap': True,
    'Horizontal_Bar_Title': "Z Score Means in Different Neighborhood Types ",
    'HorizonalBarChart': True,  
    }
    Clustering_viz(param_Harris)
    
    ended_datetime = datetime.now()
    elapsed = ended_datetime - started_datetime
    total_seconds = int(elapsed.total_seconds())
    hours, remainder = divmod(total_seconds,60*60)
    minutes, seconds = divmod(remainder,60)	
    print('GEOSNAP2NAM ended at %s %s    Elapsed %02d:%02d:%02d' % (ended_datetime.strftime('%Y-%m-%d'), ended_datetime.strftime('%H:%M:%S'), hours, minutes, seconds))
