from transformers import AutoImageProcessor, AutoModelForObjectDetection
import PIL.Image
import torch
import cv2
import os
import random
import ai_config as cfg

__models__: list[tuple[AutoModelForObjectDetection, AutoImageProcessor, str]] = []

def __get_random_color__() -> tuple[int, int, int]:
    # Get a random color (RGB)
    return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def LoadModels() -> None:
    # For each model of this service
    for i in range(len(cfg.GetAllInfosOfATask("od"))):
        # Check if the model is already loaded
        if (i < len(__models__)):
            continue
        
        # Load the model and get the info
        model, processor, device = cfg.LoadModel("od", i, AutoModelForObjectDetection, AutoImageProcessor)

        # Add the model to the list of models
        __models__.append((model, processor, device))

def Inference(Index: int, Img: str | PIL.Image.Image) -> dict[str]:
    # Load the models
    LoadModels()

    # Check the image type
    if (type(Img) == str):
        # It's a string, open the file
        image = PIL.Image.open(Img)
    elif (type(Img) == PIL.Image.Image):
        # The image is already an image, set the variable
        image = Img

        # Save the image as a temporal image
        img_name = f"tmp_od_input_{random.randint(-9999, 9999)}.png"
        image.save(img_name)

        # Set the image name
        image = img_name
    else:
        # Invalid image type
        raise Exception("Invalid image type.")

    # Open the image with OpenCV
    cv_image = cv2.imread(Img, cv2.IMREAD_COLOR)

    # Tokenize the image
    inputs = __models__[Index][1](images = [image], return_tensors = "pt")
    inputs = inputs.to(__models__[Index][2])

    # Inference the model
    outputs = __models__[Index][0](**inputs)
    target_sizes = torch.tensor([image.size[::-1]])

    # Get all the results from the processor
    results = __models__[Index][1].post_process_object_detection(outputs, target_sizes = target_sizes, threshold = 0.8)[0]
    result = []

    # For each result
    for label, box in zip(results["labels"], results["boxes"]):
        # Get the variables
        box = [round(i, 2) for i in box.tolist()]
        label = __models__[Index][0].config.id2label[label.item()]
        color = __get_random_color__()
        x = (int(box[0]), int(box[1]))
        y = (int(box[2]), int(box[3]))

        # Add variables to the results list
        result.append((str(label), (x[0], x[1], y[0], y[1])))

        # Put a rectangle and the label as text on the input image
        cv2.rectangle(cv_image, x, y, color = color, thickness = 2)
        cv2.putText(cv_image, str(label), (x[0] - 10, x[1] - 10), fontFace = cv2.FONT_HERSHEY_SIMPLEX, fontScale = 1, color = color, thickness = 2)
    
    # Save the result image as a temporal file
    file_name = "tmp_od_img_"
    file_name_id = 0

    while (os.path.exists(file_name + str(file_name_id) + ".png")):
        file_name_id += 1
    
    cv2.imwrite(file_name + str(file_name_id) + ".png", cv_image, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    
    # Read the bytes of the result image from the temporal file
    with open(file_name + str(file_name_id) + ".png", "rb") as f:
        cv_image = f.read()
        f.close()

    # Delete the temporal file
    os.remove(file_name + str(file_name_id) + ".png")

    # Return the objects and image
    return {
        "objects": result,
        "image": cv_image
    }