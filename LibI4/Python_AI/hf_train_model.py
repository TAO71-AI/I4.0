import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments, DataCollatorForLanguageModeling
from datasets import load_dataset
import ai_config as cfg
import ai_read_file as rf

dataset_name = "I4_0-base-dataset.json" # Replace with the dataset you want.
subset_name = "es" # Replace with the dataset subset name.
split = "train" # Replace with the dataset split.
column = "text" # Replace with the dataset subset column name.
model_name = "gpt2" # Replace with the model that you want to train.
local_dataset = True # True if the dataset name is the dataset path in your computer.
max_examples = 10
device = "cuda" if torch.cuda.is_available() and cfg.current_data.use_gpu_if_available else "cpu"
epochs = 1

def tokenize(examples):
    exam = examples[column] if not local_dataset else [i for i in examples[column]]
    inputs = tokenizer(
        exam,
        padding = "max_length",
        truncation = True,
        return_tensors = "pt"
    )

    return {
        "input_ids": inputs["input_ids"],
        "attention_mask": inputs["attention_mask"]
    }

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name).to(device)

tokenizer.pad_token = "[PAD]"

if (not local_dataset):
    dataset = load_dataset(dataset_name, subset_name)
    tokenized_dataset = dataset.map(tokenize, batched = True)
else:
    dataset = rf.load_dataset(dataset_name)
    tokenized_dataset = [tokenize(dataset[subset_name][split])]

data_collator = DataCollatorForLanguageModeling(tokenizer = tokenizer, mlm = False)

if (not local_dataset):
    if (max_examples > 0):
        ds = tokenized_dataset[split].shuffle().select(range(max_examples))
    else:
        ds = tokenized_dataset[split]
else:
    if (max_examples > 0):
        ds = tokenized_dataset[:max_examples]
    else:
        ds = tokenized_dataset

training_args = TrainingArguments(
    output_dir = "./trained_hf_model",
    overwrite_output_dir = True,
    num_train_epochs = epochs,
    per_device_train_batch_size = 2,
    save_steps = 1000,
    save_total_limit = 1
)
trainer = Trainer(
    model = model,
    args = training_args,
    data_collator = data_collator,
    train_dataset = ds
)

trainer.train()
trainer.save_model()