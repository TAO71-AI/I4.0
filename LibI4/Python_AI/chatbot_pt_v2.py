import torch
import torch.nn as nn
import torch.optim as optim
import ai_read_file as rf
import ai_config as cfg

# Create GPT model
class GPT(nn.Module):
    def __init__(self, vocab_size, embedding_size, hidden_size, num_layers) -> None:
        super().__init__()

        self.embedding = nn.Embedding(vocab_size, embedding_size)
        self.transformer = nn.Transformer(hidden_size, num_layers)
        self.fc = nn.Linear(hidden_size, vocab_size)
        self.trained = False
    
    def forward(self, src, tgt) -> torch.Tensor:
        src = self.embedding(src)
        tgt = self.embedding(tgt)
        res = self.transformer(src, tgt)
        res = self.fc(res)

        return res

# Load dataset
dataset = rf.read_lines_from_file(cfg.current_data.tf_data_file)

# Tokenizer and detokenizer
_word_to_index_ = {}
_index_to_word_ = {}

for line in dataset:
    for word in line.split():
        if (word not in _word_to_index_):
            index = len(_word_to_index_)

            _word_to_index_[word] = index
            _index_to_word_[index] = word

X = torch.tensor([_word_to_index_[word] for line in dataset for word in line.split()[:-1]])
Y = torch.tensor([_word_to_index_[word] for line in dataset for word in line.split()[1:]])

# Define parameters
vocab_size = len(_word_to_index_)
embedding_size = 128
hidden_size = 128
num_layers = 1

# Define model, loss and optimizer
model = GPT(vocab_size, embedding_size, hidden_size, num_layers)
cel = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr = 0.001)

# Train the model
def TrainModel() -> None:
    for epoch in range(cfg.current_data.tf_epochs):
        optimizer.zero_grad()

        outputs = model(X, Y)
        loss = cel(outputs.view(-1, vocab_size), Y)

        loss.backward()
        optimizer.step()

        print("Epoch #" + str(epoch) + ": " + str(loss.item()))
    
    model.trained = True

# Save the model
def SaveModel(ModelName: str = "pt_model") -> None:
    torch.save(model.state_dict(), ModelName + ".pth")

# Load the model
def LoadModel(ModelName: str = "pt_model"):
    model.load_state_dict(torch.load(ModelName + ".pth"))

# Response
def GetResponse(Prompt: str) -> str:
    prompt = Prompt
    response = ""
    length = 0

    while (length <= cfg.current_data.max_length):
        prompt_tensor = torch.tensor([_word_to_index_[word] for word in prompt.split()])
        response = model(prompt_tensor.unsqueeze(0), prompt_tensor.unsqueeze(0))
        next_word_index = torch.argmax(response[-1]).item()
        next_word = _index_to_word_.get(next_word_index, "<unk>")

        if (next_word.lower() == "<unk>"):
            break

        prompt += " " + next_word
        response += next_word + " "
    
    return response