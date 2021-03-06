import argparse
import time
from pathlib import Path
import os
import cv2
import torch
import torch.backends.cudnn as cudnn
import numpy as np
from numpy import random
from PIL import Image
from models.experimental import attempt_load
from utils.datasets import LoadStreams, LoadImages, letterbox
from utils.general import check_img_size, check_requirements, check_imshow, non_max_suppression, apply_classifier, \
    scale_coords, xyxy2xywh, strip_optimizer, set_logging, increment_path, save_one_box
from utils.plots import colors, plot_one_box
from utils.torch_utils import select_device, load_classifier, time_synchronized
import matplotlib.pyplot as plt

class LiveYolo():
    def __init__(self):
        folder_path = "5l_640_10" #IRASYTI MODELIO PAVADINIMA CIA
        self.default_model_path = f'live_models/{folder_path}/weights/best.pt'
        self.device = ''
        self.im_size = int(folder_path.split("_")[1])
        self.conf_thresh = 0.25
        self.iou_thresh = 0.3


    def load(self, model_path=None):
        set_logging()
        self.device = select_device(self.device)
        self.half = self.device.type != 'cpu'  # half precision only supported on CUDA

        if model_path == None:
            model_path = self.default_model_path
        self.model   = attempt_load(model_path, map_location=self.device);self.names = self.model.module.names if hasattr(self.model, 'module') else self.model.names
        self.stride = int(self.model.stride.max())  # model stride

    def run_on_single_frame(self, frame):
        frame = np.ascontiguousarray(np.asarray(frame)[:,:,::-1])
        imgsz = check_img_size(self.im_size, s=self.stride)  # check img_size
          # get class names
        if self.half:
            self.model.half()  # to FP16

        img = letterbox(frame, self.im_size,self.stride)[0]
        img = img.transpose(2, 0, 1)
        img = np.ascontiguousarray(img)


        # Run inference
        if self.device.type != 'cpu':
            self.model(torch.zeros(1, 3, imgsz, imgsz).to(self.device).type_as(next(self.model.parameters())))  # run once
        t0 = time.time()

        img = torch.from_numpy(img).to(self.device)
        img = img.half() if self.half else img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)
            # Inference
        t1 = time_synchronized()
        pred = self.model(img)[0]#add augment=store_true to replicate original


            # Apply NMS
        pred = non_max_suppression(pred, self.conf_thresh, self.iou_thresh, classes=None, agnostic=False)
        t2 = time_synchronized()
        print("t2-t1", t2-t1)

            # Process detections
        for i, det in enumerate(pred):  # detections per image
                #p, s, im0, frame = path, '', im0s.copy(), getattr(dataset, 'frame', 0)
                #print("p", p, "s", s, "im0", im0, "frame", frame)
                #print("det", det)
                #gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
            if len(det):
                    # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], frame.shape).round()

                #for *xyxy, conf, cls in reversed(det):
                    #c = int(cls)
                    #label = f'{self.names[c]} {conf:.2f}'
                    #p = plot_one_box(xyxy, frame, label=label, color=colors(c, True), line_thickness=2)


        pred = [item.cpu() for item in pred]
        return pred #coords, classes, probs


if __name__ == '__main__':

    check_requirements(exclude=('tensorboard', 'pycocotools', 'thop'))
    detector = LiveYolo()
    detector.load()
    im = Image.open('./im2.jpg')

    #print(im.shape, "SHAPEE")
    with torch.no_grad():
        coords,classes,probs = detector.run_on_single_frame(im)
    print(coords,classes,probs)
