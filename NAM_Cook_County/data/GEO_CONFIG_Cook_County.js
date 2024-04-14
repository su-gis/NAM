// Define the number of maps and some configuration parameters that you want to visualize.

var SubjectName = "NEIGHBORHOOD";
var InitialLayers = ["INC", "1990", "2000", "2010", "2019"];
var Type_Labels = {};
//var Type_Labels = {"T0": "0.White Rich Owner", "T1": "1.White Hispanic Aging Suburban", "T2": "2.Asian Elite Renter", "T3": "3.Hispanic Laborer", "T4": "4.Black Poor", "T5": "5.Black Owner"};

/* Map Extent and Zoom level will be automatically adjusted when you do not define map center and zoom level */
//var Initial_map_center = [34.0522, -117.9];  
//var Initial_map_zoom_level = 8;   

var allMetros = false;                                      //choropleth map: Maps representing INC of all metros
var Index_of_neighborhood_change = true;					//choropleth map: Maps representing index of neighborhood Change
var Qualitative_Maps = true;							//choropleth map: Maps representing clustering result  
var Distribution_INC1 = false;								//density chart: INC changes as the map extent changes 
var Distribution_INC2_different_period = false;				//density chart: INC changes by different years
var Distribution_INC2_different_cluster = false;				//density chart: INC changes by different clusters
var Standardization = false;
var Stacked_Chart = true;				//stacked chart: Temporal Change in Neighborhoods over years
var Transition_Chart = false;
var Parallel_Categories_Diagram = true;	//parallel categories diagram
var Chord_Diagram = true;					//chord diagram
var HeatmapTitle = "Z Score Means across Different Neighborhood Types";
var Heatmap = true;                    //heatmap: Z Score Means across Clusters
var Horizontal_Bar_Title = "Z Score Means in Different Neighborhood Types ";
var HorizonalBarChart = true;                    //barchart: Z Score Means of Each Cluster


var Num_Of_Decimal_Places = 2;                             // default = 2

var Map_width  = "420px";                                  // min 350px
var Map_height = "410px";                                  // min 300px


/////////////////////////////////////////////////////////////////
// Options for only INC map                                    //
/////////////////////////////////////////////////////////////////

//option for class(the classification method): equal, quantile, std, arithmetic, geometric, quantile
//option for count(the number of classes): 1 to 9
//options for color: Green, Blue, Orange, Red, Pink

var mapAclassification = {class: 'equal', count: 8, color: 'Red'};