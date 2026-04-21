import os
import cv2
import random
import matplotlib.pyplot as plt
from src.config import YOLO_DATASET_DIR


def show_yolo_samples(split="train",num_images=6):

    IMG_DIR=os.path.join(YOLO_DATASET_DIR,split,"images")
    LABEL_DIR=os.path.join(YOLO_DATASET_DIR,split,"labels")

    imgs=[f for f in os.listdir(IMG_DIR) if f.endswith(".png")]

    samples=random.sample(imgs,min(num_images,len(imgs)))

    cols=3
    rows=(len(samples)+cols-1)//cols

    plt.figure(figsize=(5*cols,5*rows))

    for i,img_file in enumerate(samples):

        img_path=os.path.join(IMG_DIR,img_file)
        label_path=os.path.join(LABEL_DIR,img_file.replace(".png",".txt"))

        img=cv2.imread(img_path)
        img=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)

        if os.path.exists(label_path):

            with open(label_path) as f:
                lines=f.readlines()

            for line in lines:

                cls,x_c,y_c,w,h=map(float,line.split())

                x_center=x_c*img.shape[1]
                y_center=y_c*img.shape[0]

                bw=w*img.shape[1]
                bh=h*img.shape[0]

                x1=int(x_center-bw/2)
                y1=int(y_center-bh/2)

                x2=int(x_center+bw/2)
                y2=int(y_center+bh/2)

                cv2.rectangle(img,(x1,y1),(x2,y2),(255,0,0),2)

        plt.subplot(rows,cols,i+1)
        plt.imshow(img)
        plt.axis("off")

    plt.tight_layout()
    plt.show()