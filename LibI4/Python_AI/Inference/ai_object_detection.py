from transformers import AutoImageProcessor, AutoModelForObjectDetection
import PIL.Image
import torch
import cv2
import os
import random
import ai_config as cfg

processor: AutoImageProcessor = None
model: AutoModelForObjectDetection = None
device: str = "cpu"

def __get_random_color__() -> tuple[int, int, int]:
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def LoadModel() -> None:
    global processor, model, device

    if (not cfg.current_data["prompt_order"].__contains__("od")):
        raise Exception("Model is not in 'prompt_order'.")

    if (processor != None and model != None):
        return

    if (cfg.current_data["print_loading_message"]):
        print("Loading model 'object detection'...")

    data = cfg.LoadModel("od", cfg.current_data["object_detection_model"], AutoModelForObjectDetection, AutoImageProcessor)

    model = data[0]
    processor = data[1]
    device = data[2]

    if (cfg.current_data["print_loading_message"]):
        print("   Loaded model on device '" + device + "'.")

def MakePrompt(img: str) -> dict[str]:
    LoadModel()

    image = PIL.Image.open(img)
    cv_image = cv2.imread(img, cv2.IMREAD_COLOR)
    inputs = processor(images = [image], return_tensors = "pt")
    inputs = inputs.to(device)

    outputs = model(**inputs)
    target_sizes = torch.tensor([image.size[::-1]])
    results = processor.post_process_object_detection(outputs, target_sizes = target_sizes, threshold = 0.8)[0]
    result = []

    for label, box in zip(results["labels"], results["boxes"]):
        box = [round(i, 2) for i in box.tolist()]
        label = model.config.id2label[label.item()]
        color = __get_random_color__()
        x = (int(box[0]), int(box[1]))
        y = (int(box[2]), int(box[3]))

        result.append((str(label), (x[0], x[1], y[0], y[1])))
        cv2.rectangle(cv_image, x, y, color = color, thickness = 2)
        cv2.putText(cv_image, str(label), (x[0] - 10, x[1] - 10), fontFace = cv2.FONT_HERSHEY_SIMPLEX, fontScale = 1, color = color, thickness = 2)
    
    file_name = "tmp_od_img_"
    file_name_id = 0

    while (os.path.exists(file_name + str(file_name_id) + ".png")):
        file_name_id += 1
    
    cv2.imwrite(file_name + str(file_name_id) + ".png", cv_image, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    
    with open(file_name + str(file_name_id) + ".png", "rb") as f:
        cv_image = f.read()
        f.close()

    os.remove(file_name + str(file_name_id) + ".png")
    return {
        "objects": result,
        "image": cv_image
    }