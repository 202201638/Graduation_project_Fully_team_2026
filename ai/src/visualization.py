import os
import cv2
import matplotlib.pyplot as plt
from src.config import PNG_DIR


def show_pneumonia_example(df):

    png_files = os.listdir(PNG_DIR)

    patient_ids = [f.replace(".png", "") for f in png_files]

    pneumonia_cases = df[
        (df["Target"] == 1) &
        (df["patientId"].isin(patient_ids))
    ]

    if pneumonia_cases.empty:
        print("No pneumonia cases with available PNG images found.")
        return

    # pick a random pneumonia case to avoid index issues
    sample = pneumonia_cases.sample(1).iloc[0]

    patient_id = sample["patientId"]

    img = cv2.imread(os.path.join(PNG_DIR, f"{patient_id}.png"))

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    boxes = df[df["patientId"] == patient_id]

    for _, row in boxes.iterrows():

        if row["Target"] == 1:

            x = int(row["x"])
            y = int(row["y"])
            w = int(row["width"])
            h = int(row["height"])

            cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),3)

    plt.imshow(img)
    plt.axis("off")
    plt.show()