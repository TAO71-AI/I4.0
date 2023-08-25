from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments, DataCollatorWithPadding
import torch
import ai_read_file as rf

model_name: str = "gpt2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)
collator = DataCollatorWithPadding(tokenizer)

tokenizer.pad_token = tokenizer.eos_token

train_file = "tf_train_data_es.txt"
train_data: list[str] = rf.read_lines_from_file(train_file)
val_data: list[str] = train_data[0:int(len(train_data) / 2)]

class Dataset(torch.utils.data.Dataset):
    def __init__(self, train_data: list[str]) -> None:
        self.encodings = tokenizer(train_data, padding = True, truncation = True, return_tensors = "pt")
        self.vocab_size = len(sorted(set(train_data)))
    
    def __len__(self) -> int:
        return len(self.encodings["input_ids"])
    
    def __getitem__(self, idx):
        return {
            "input": {key: val[idx] for key, val in self.encodings.items()},
            "target": {key: val[idx] for key, val in self.encodings.items()}
        }

dataset = Dataset(train_data)
edataset = Dataset(val_data)
training_args = TrainingArguments(
    per_device_train_batch_size = 4,
    output_dir = "./my_custom_hf_" + model_name + "_model",
    overwrite_output_dir = True,
    num_train_epochs = 1
)
trainer = Trainer(
    model = model,
    args = training_args,
    train_dataset = dataset,
    eval_dataset = edataset,
    tokenizer = tokenizer,
    data_collator = collator
)

print("Vocab size: " + str(dataset.vocab_size))

trainer.train()
print("Test your model! When done write 'exit'.")

while True:
    prompt = input("You: ")

    if (prompt.strip().lower() == "exit"):
        break

    input_ids = tokenizer.encode(prompt, return_tensors = "pt")
    output = model.generate(input_ids, max_length = 100, num_return_sequences = 1)
    generated_text = tokenizer.decode(output[0], skip_special_tokens = True)

    print("AI: " + generated_text)