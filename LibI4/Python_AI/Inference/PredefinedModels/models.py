import yaml
import os

FilesDir = os.path.dirname(__file__)

with open(os.path.join(FilesDir, "text2img_sdcpp.yaml"), "r") as f:
    Text2Image_SDCPP: dict[str, dict[str, any]] = yaml.safe_load(f)

with open(os.path.join(FilesDir, "chatbot_nf_lcpp.yaml"), "r") as f:
    Chatbot_NF_LCPP: dict[str, dict[str, any]] = yaml.safe_load(f)