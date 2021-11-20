import os, json
import numpy as np
import pandas as pd
from PIL import Image
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
from labels import labels
from utils import *

DEFAULT_IMG = Image.open("default_img.jpg")
fig = px.imshow(DEFAULT_IMG)

def get_img_labels(img_name,data_subset):
    # given an image name, return a list of all object bounding boxes
    bboxes = []
    categories = []
    colors = []
    img_basenme = os.path.basename(img_name).split('.')[0]
    if data_subset == 'train' and img_basenme in DET_TRAIN_JSON.keys():
        labels_json = DET_TRAIN_JSON[img_basenme]['labels']
    elif img_basenme in DET_VAL_JSON.keys():
        labels_json = DET_VAL_JSON[img_basenme]['labels']
    else:
        # in case bad image selected, return empty lists
        return bboxes, categories, colors
    for label in labels_json:
        bbox_json = label['box2d']
        bbox = [x for x in bbox_json.values()]
        bboxes.append(bbox)
        category = label['category']
        if category in PERSON_LABELS:
            color = "red"
        elif category in VEHICLE_LABELS:
            color = "blue"
        else:
            color = "green"
        colors.append(color)
        categories.append(category)
    return bboxes, categories, colors



# Start Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO],
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}])



app.layout = dbc.Container([
    dbc.Row(html.H1("BDD100K Visualization Webapp"), className='text-primary text-center'),
    # dbc.Row(html.P("A Dash webapp that helps exploring the Berkley Deep Drive dataset."), className='text-left mb-4'),

    dbc.Row([
        dbc.Col([
            html.B("Select label type:",  className='font-weight-bold'),
            dcc.RadioItems(id='label-type', labelClassName="mr-3", inputClassName="m-2",  options=[
                {'label': 'Semantic Segmentation', 'value': 'sem_seg'},
                {'label': 'Instance Segmentation', 'value': 'ins_seg'},
                {'label': 'Object Detection', 'value': 'obj_det'}])
        ], xs=12, sm=12, md=12, lg=5, xl=5),
        
        dbc.Col([
            html.B("Select data subset:",  className='font-weight-bold'),
            dcc.RadioItems(id='train-val', labelClassName="mr-3", inputClassName="m-2", options=[
                {'label': 'Training', 'value': 'train'},
                {'label': 'Validation', 'value': 'val'}])
        ], xs=12, sm=12, md=12, lg=5, xl=5),

    ], className='pb-4', justify='around'),
    
    dbc.Row([
        dbc.Col([dcc.Loading(
            id="loading-1",
            type="default",
            children=dcc.Dropdown(id='img-name', clearable=False, placeholder='select image', options=[]))
        ], xs=12, sm=12, md=12, lg=5, xl=5),

        dbc.Col([
            html.B('Mask alpha:', className='text-center'),
            dcc.Slider(id='alpha-slider', min=0, max=255, step=1, value=70,  
                    tooltip={"placement": "bottom", "always_visible": True}, marks={0: '0', 255: '255'})
        ], xs=12, sm=12, md=12, lg=5, xl=5)
    ], align="center"),

    dbc.Row(dcc.Graph(id='main-image', figure=fig, style={"height": "720px","width": "1280px", "margin-left": "auto", "margin-right": "auto"})),
])

@app.callback(
    Output('img-name', 'options'),
    Input('label-type', 'value'),
    Input('train-val', 'value'))
def update_file_list(label_type,data_subset):
    if label_type is None or data_subset is None:
        return []
    # determine img_dir
    if "seg" in label_type:
        return FILES[f'seg_{data_subset}']
        # label_dir = os.path.join(DATA_DIR, "labels",label_type, "colormaps",data_subset)
    elif "obj_det" in label_type:
        return FILES[f'det_{data_subset}']
    else:
        return []

@app.callback(
    Output('alpha-slider', 'disabled'),
    Input('label-type', 'value'),
)
def update_slider(label_type):
    if label_type == 'obj_det':
        return True
    else:
        return False

@app.callback(
    Output('main-image', 'figure'),
    Input('img-name', 'value'),
    Input('label-type', 'value'),
    Input('train-val', 'value'),
    Input('alpha-slider', 'value'),)
def update_graph(img_name,label_type,data_subset,alpha):
    if img_name is not None and os.path.exists(img_name):
        img = Image.open(img_name)

        if "seg" in label_type:
            #  semantic/instance segmentation - plot colormaps
            label_dir = os.path.join(DATA_DIR,"labels",label_type, "colormaps", data_subset)
            png_img_name = os.path.basename(img_name).replace(".jpg", ".png")
            label_img = os.path.join(label_dir,png_img_name)
            if os.path.exists(label_img):
                img_seg = Image.open(label_img).convert("RGB")
                img.putalpha(255-alpha)
                img_seg.putalpha(alpha)
                img.alpha_composite(img_seg,(0,0))
        else:
            bboxes, categories, colors = get_img_labels(img_name, data_subset)


        fig = px.imshow(img)

        if label_type == "obj_det":
            existing_classes = set()
            for i in range(len(bboxes)):
                label = categories[i]
                # only display legend when it's not in the existing classes
                showlegend = label not in existing_classes
                add_bbox(fig, bboxes[i],opacity=0.7, group=label, name=label, color=colors[i], showlegend=showlegend, text=label)
                existing_classes.add(label)                
    else:
        fig = px.imshow(DEFAULT_IMG)
    return fig



if __name__ == '__main__':
    DATA_DIR = r"D:\\Code\\WiSense\\bbd100k_dataset\\bdd100k"
    # DATA_DIR = "dummy_data"
    print("Listing images in directories...")
    FILES = {}
    FILES['seg_train'] = get_img_filenames(os.path.join(DATA_DIR, "images", "10k" , "train"))
    FILES['det_train'] = get_img_filenames(os.path.join(DATA_DIR, "images", "100k", "train"))
    FILES['seg_val']   = get_img_filenames(os.path.join(DATA_DIR, "images", "10k" , "val"))
    FILES['det_val']   = get_img_filenames(os.path.join(DATA_DIR, "images", "100k", "val"))
    print("Initialzing object detection JSON labels")
    DET_TRAIN_JSON, DET_VAL_JSON = init_json_labels(DATA_DIR)
    print("done!")
    app.run_server(debug=True, use_reloader=False)