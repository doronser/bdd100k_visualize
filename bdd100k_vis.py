import os, json 
from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw

# Future development items:
#    display json metadata (weather, scene, timeofday)
#    display info on classes in current image
#    allow filtering images

class bdd100k_vis(Tk):
    def __init__(self,dataset_path='dummy_data'):
        super().__init__()
        ##################
        # init constants #
        ##################
        # default values
        self.dataset_dir = dataset_path
        self.dataset = ""           # train/val
        self.label_type = ""        # sem_seg/ins_seg/obj_det
        self.alpha = 70             # alpha value for mask overlay
        self.label_dir = None 
        self.img_dir = None 
        self.img_name = None
        self.hex_dict = label_to_hex() # used for semantic segmentation color legend
        self.title('BDD100K Visualization Tool') # GUI window title
        #  used for drop down menu event handling
        self.dataset_dict = {"Train": "train", "Validation": "val","":""}
        self.label_dict = {"Semantic Segmentation": "sem_seg", "Instance Segmentation": "ins_seg", "Object Detection": "obj_det", "":""}
        # object detection label categories
        self.vehicle_labels = ['car', 'bus', 'train', 'trailer', 'bicycle', 'motorcycle', 'truck',  'other vehicle']
        self.person_labels = ['pedestrian', 'rider', 'other person']
        self.misc_labels = [ 'traffic light', 'traffic sign']

        # get json labels for object detection - takes ~10 seconds
        # TODO: Optimize runtime (threads? partial loading?)
        self.init_json_labels()

        # init GUI elements
        self.create_frames()
        self.init_dispFrame()
        self.init_semSegFrame()
        self.init_ctrlFrame()
    
    
    
    ####################
    # Init GUI Widgets #
    ####################
    def create_frames(self):
        # init paned window
        self.panedwindow = ttk.Panedwindow(self, orient = HORIZONTAL)
        self.panedwindow.pack(fill = BOTH, expand = True)

        # define 3 frames for GUI
        self.dispFrame = ttk.Frame(self.panedwindow, width = 540, height = 960, relief = SUNKEN)
        self.ctrlFrame = ttk.Frame(self.panedwindow,height=300, width=100, relief = SUNKEN)
        self.semSegFrame = ttk.Frame(self.panedwindow,height=300, width=100, relief = SUNKEN)

        # populate frames in GUI
        self.panedwindow.add(self.ctrlFrame, weight = 0)
        self.panedwindow.add(self.dispFrame, weight = 1)
        self.panedwindow.insert(1,self.semSegFrame)

    def init_dispFrame(self):
        # init display frame elements
        img = Image.open("default_img.jpg").resize((960, 540), Image.ANTIALIAS)
        self.disp_img = ImageTk.PhotoImage(img)
        self.display_obj = ttk.Label(self.dispFrame,image=self.disp_img, text="Welcome", compound="bottom", font=('Helvetica', 12))
        self.display_obj.pack()

    def init_semSegFrame(self):
        # init sem_seg frame elements
        ttk.Label(self.semSegFrame, text="Semantic Segmentation Legend", font=('Helvetica', 12)).pack()
        for hex_code in sorted(self.hex_dict.keys()):
            ttk.Label(self.semSegFrame, text=self.hex_dict[hex_code] ,background=hex_code,foreground="white",font=('Helvetica', 10)).pack()

    def init_ctrlFrame(self):
                ###############################
        # init control frame elements #
        ###############################
        
        #### init comboBoxes
        # label type drop down menu + text
        label_text = ttk.Label(self.ctrlFrame, text="Label Type:")
        label_text.grid(column=0,row=0, padx=5, pady=5)
        label_type = StringVar()
        self.label_combobox = ttk.Combobox(self.ctrlFrame, textvariable = label_type, width =25, state= "readonly")
        self.label_combobox['values'] = ('Instance Segmentation', 'Semantic Segmentation', 'Object Detection')
        self.label_combobox.grid(column=0,row=1)

        # train/test drop down menu + text
        train_val_text = ttk.Label(self.ctrlFrame, text="Select train/val:")
        train_val_text.grid(column=0,row=2, padx=5, pady=5)
        train_val = StringVar()
        self.dataset_combobox = ttk.Combobox(self.ctrlFrame, textvariable = train_val, width =25, state= "readonly")
        self.dataset_combobox['values'] = ('Train','Validation')
        self.dataset_combobox.grid(column=0,row=3)

        # init alpha slider + text
        self.alpha_text = ttk.Label(self.ctrlFrame, text="Mask alpha: 70")
        self.alpha_text.grid(column=0,row=4, padx=5, pady=5)
        alpha_value = IntVar
        self.scale = ttk.Scale(self.ctrlFrame, orient = HORIZONTAL,length = 100, variable = alpha_value, from_ = 0, to = 255)
        self.scale.set(70)
        self.scale.grid(column=0,row=5)

        # image list
        self.img_list_text = ttk.Label(self.ctrlFrame, text="Image List:")
        self.img_list_text.grid(column=0,row=6, padx=5, pady=5)
        self.img_list = Listbox(self.ctrlFrame, height=20)
        self.img_list.grid(column=0, row=10, sticky=(W,E))
        self.img_scroll = ttk.Scrollbar(self.ctrlFrame, orient=VERTICAL, command=self.img_list.yview)
        self.img_scroll.grid(column=1, row=10, sticky=(N,S))
        self.img_list['yscrollcommand'] = self.img_scroll.set

        # object detection legend
        #  TODO: move to notebook widget (tabbed window) with semantic segmentation legend
        obj_det_lgd = ttk.Label(self.ctrlFrame, text="Object Detection Legend")
        obj_det_lgd.grid(column=0,row=11, padx=5, pady=5)
        vehicle_text = ttk.Label(self.ctrlFrame, text="Vehicle", background="blue",foreground="white",font=('Helvetica', 10))
        vehicle_text.grid(column=0,row=12)
        person_text = ttk.Label(self.ctrlFrame, text="Person", background="red",foreground="white",font=('Helvetica', 10))
        person_text.grid(column=0,row=13)
        misc_text = ttk.Label(self.ctrlFrame, text="Traffic Sign/Light", background="green",foreground="white",font=('Helvetica', 10))
        misc_text.grid(column=0,row=14)

        # assign callbacks
        self.label_combobox.bind("<<ComboboxSelected>>",self.menu_callback)
        self.dataset_combobox.bind("<<ComboboxSelected>>",self.menu_callback)
        self.scale.config(command=self.plot_img)
        self.img_list.bind("<<ListboxSelect>>", self.plot_img)



    ####################
    # helper functions #
    ####################
    def init_json_labels(self):
        # parse json labels to a nice format
        # output: dictionary that maps img_name to it's json object
        print("initialzing object detection JSON labels")
        json_path = os.path.join(self.dataset_dir, "labels", "det_20")
        train_file = open(os.path.join(json_path,"det_train.json"))
        train_data = json.loads(train_file.read())
        train_json_dict = {}
        for json_obj in train_data:
            key = json_obj['name'].split(".")[0]
            train_json_dict[key] = json_obj
        self.train_json = train_json_dict
        
        val_file = open(os.path.join(json_path,"det_val.json"))
        val_data = json.loads(val_file.read())
        val_json_dict = {}
        for json_obj in val_data:
            key = json_obj['name'].split(".")[0]
            val_json_dict[key] = json_obj
        self.val_json = val_json_dict

    def get_img_labels(self):
        # given an image name, return a list of all object bounding boxes
        bboxes = []
        colors = []
        if self.dataset == 'train':
            labels_json = self.train_json[self.img_name]['labels']
        else:
            labels_json = self.val_json[self.img_name]['labels']
        for label in labels_json:
            bbox_json = label['box2d']
            bbox = [x for x in bbox_json.values()]
            bboxes.append(bbox)
            category = label['category']
            if category in self.person_labels:
                color = "red"
            elif category in self.vehicle_labels:
                color = "blue"
            else:
                color = "green"
            colors.append(color)
        return bboxes, colors

    def populate_img_list(self):
        #  update list of image names based on current directory
            if self.img_dir is not None and os.path.exists(self.img_dir):
                img_files = os.listdir(self.img_dir)
                self.img_list.delete(0,END)
                print(f"populating {len(img_files)} images from {self.img_dir}")
                for img_file in img_files:
                    img_basenme = img_file.split(".")[0]
                    self.img_list.insert(END,img_basenme)

    #############
    # callbacks #
    #############
    def plot_img(self,event):
        # plot image + labels to GUI
        #   for segmentation tasks: alpha composite of image and color mask
        #   for object detection: plot bounding boxes over image
        if len(self.img_list.curselection()) > 0:
            self.img_name = self.img_list.get(self.img_list.curselection())

        # update alpha value
        self.alpha = int(self.scale.get())
        self.alpha_text['text'] = f"Mask alpha: {self.alpha}"

        img_path = os.path.join(self.img_dir, f"{self.img_name}.jpg")
        if os.path.exists(img_path):
            i = Image.open(img_path)
        else:
            print("image not found!")
            return

        if "seg" in self.label_type:
            #  semantic/instance segmentation - plot colormaps
            label_path = os.path.join(self.label_dir, f"{self.img_name}.png")
            if os.path.exists(label_path):
                i = Image.open(img_path)
                i_seg = Image.open(label_path).convert("RGB")
                i.putalpha(255-self.alpha)
                i_seg.putalpha(self.alpha)
                i.alpha_composite(i_seg,(0,0))
        else:
            # object detection - plot bounding boxes
            draw = ImageDraw.Draw(i)
            bboxes, colors = self.get_img_labels()
            for idx in range(len(bboxes)):
                bbox = bboxes[idx]
                draw.rectangle(bbox,outline=colors[idx], width=2)
        
        # display image + labels on screen
        img = i.resize((960, 540), Image.ANTIALIAS)
        self.disp_img = ImageTk.PhotoImage(img)
        self.display_obj['image'] = self.disp_img
        self.display_obj['text'] = self.img_name

    def menu_callback(self,event):
        #  parse train/test value
        dataset_txt = self.dataset_combobox.get()
        self.dataset = self.dataset_dict[dataset_txt]

        # determine label type (sem_seg/ins_seg/obj_det)
        label_txt = self.label_combobox.get()
        self.label_type = self.label_dict[label_txt]

        # determine img_dir
        if "seg" in self.label_type:
            self.img_dir = os.path.join(self.dataset_dir, "images","10k",self.dataset)
            self.label_dir = os.path.join(self.dataset_dir, "labels",self.label_type, "colormaps",self.dataset)
        elif "obj_det" in self.label_type:
            self.img_dir = os.path.join(self.dataset_dir, "images","100k",self.dataset)
        else:
            self.img_dir = None

        # update img_list
        if label_txt is not None and dataset_txt is not None:
            self.populate_img_list()

#use dataset metadata to get hex colors for semantic segmentation
def label_to_hex():
    from labels import labels
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


if __name__ == '__main__':
    # app = bdd100k_vis("D:\\Code\\WiSense\\bbd100k_dataset\\bdd100k")
    app = bdd100k_vis()
    app.mainloop()