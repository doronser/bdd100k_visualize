import pickle, json, timeit, os
import dash
from dash import dcc
from dash import html
import plotly.graph_objects as go
from labels import labels
import pandas as pd

VEHICLE_LABELS = ['car', 'bus', 'train', 'trailer', 'bicycle', 'motorcycle', 'truck',  'other vehicle']
PERSON_LABELS = ['person', 'pedestrian', 'rider', 'other person']
MISC_LABELS = ['traffic light', 'traffic sign']

#use dataset metadata to get hex colors for semantic segmentation
def label_to_hex():
    hex_dict = {}
    for label in labels:
        label_color = label.color
        label_name = label.name
        label_color_hex = f"#{label_color[0]:02x}{label_color[1]:02x}{label_color[2]:02x}"
        if label_color_hex in hex_dict.keys():
            hex_dict[label_color_hex].append(label_name)
        else:
            hex_dict[label_color_hex] = [label_name]
    return hex_dict

def init_json_labels(data_dir):
    # TODO: improve runtime - use pickle to save structured data?
    # parse json labels to a nice format
    # output: dictionary that maps img_name to it's json object
    json_path = os.path.join(data_dir, "labels", "det_20")
    train_file = open(os.path.join(json_path,"det_train.json"))
    train_data = json.loads(train_file.read())
    train_json_dict = {}
    for json_obj in train_data:
        key = json_obj['name'].split(".")[0]
        train_json_dict[key] = json_obj
    train_json = train_json_dict
    
    val_file = open(os.path.join(json_path,"det_val.json"))
    val_data = json.loads(val_file.read())
    val_json_dict = {}
    for json_obj in val_data:
        key = json_obj['name'].split(".")[0]
        val_json_dict[key] = json_obj
    val_json = val_json_dict
    return train_json, val_json

#generate file lists for dropdown menu
def get_img_filenames(img_dir):
    # input: image directory
    # output: dictionary where key = image basename, value = image filename (fullpath)
    # description: the dictionary is used in the dropdown menu to select which image to display
    if os.path.exists(img_dir):
        img_files = os.listdir(img_dir)
        print(f"found {len(img_files)} images")
        return [{'label': img_name, 'value': os.path.join(img_dir,img_name)} for img_name in img_files]
    else:
        return []

def add_bbox(fig, bbox, 
            showlegend=True, name=None, color=None, 
            opacity=0.5, group=None, text=None):
    x0, y0, x1, y1 = bbox
    fig.add_trace(go.Scatter(
        x=[x0, x1, x1, x0, x0],
        y=[y0, y0, y1, y1, y0],
        mode="lines",
        fill="toself",
        opacity=opacity,
        marker_color=color,
        hoveron="fills",
        name=name,
        hoverlabel_namelength=0,
        text=text,
        legendgroup=group,
        showlegend=showlegend,
    ))

def json_to_df(filename):
    file_basename = os.path.basename(filename).split('.')[0]
    with open(filename,"r") as fh:
        labels_json = json.loads(fh.read())
    print("opened the file")

    # fix missing labels for train ds
    if 'train' in filename:
        for i in range(len(labels_json)):
            json_obj = labels_json[i]
            if 'labels' not in json_obj.keys():
                print(f"object {i}: {json_obj['name']} is missing labels!")
                json_obj['labels'] = [{}]

    meta_list = ['name','attributes']
    df = pd.json_normalize(labels_json, record_path=['labels'], meta = meta_list, errors='ignore')
    print(f"generated base df. total number of images: {len(df.name.unique())}")
    new_cols = pd.json_normalize(df.attributes)
    print(f"generated att df.")
    data_df = pd.concat([df.drop(columns=['id','attributes']),new_cols], axis=1)
    print(f"merged dfs. total number of images: {len(data_df.name.unique())}")

    # rename + reorder columns
    data_df.columns = ['category', 'occluded', 'truncated', 'trafficLightColor', 'x1', 'y1', 'x2', 'y2', 'crowd', 'name', 'weather', 'timeofday','scene']
    data_df = data_df[['name', 'category', 'weather', 'timeofday','scene', 'occluded', 'truncated', 'crowd', 'trafficLightColor', 'x1', 'y1', 'x2', 'y2']]
    data_df = data_df.set_index('name') # for faster querying by img_name
    data_df.to_pickle(f"{file_basename}2.pkl")
    return


if __name__ == "__main__":
    base_dir = r"D:\Code\WiSense\bbd100k_dataset\bdd100k\labels\det_20"
    print("converting validation json to pickle DataFarme")
    t0 = timeit.default_timer()
    json_to_df(f"{base_dir}\det_val.json")
    t1 = timeit.default_timer()
    print('Time: ', t1 - t0)  
    print("converting train json to pickle DataFarme")
    json_to_df(f"{base_dir}\det_train.json")
    t2 = timeit.default_timer()
    print('Time: ', t2 - t1)  
