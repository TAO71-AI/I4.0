import torch
import torch.nn as nn
import numpy as np
import os
import ai_read_file as rf
import ai_config as cfg

# Get train data from file
train_data: list[str] = rf.read_lines_from_file(cfg.current_data.tf_data_file)
train_data_full: str = "".join(i + "\n" for i in train_data)
model_loaded: bool = False

# Create chars
chars = sorted(list(set(train_data_full)))
vocab_size = len(chars)

# Encoder/Decoder
encoder = {ch:i for i, ch in enumerate(chars)}
decoder = {i:ch for i, ch in enumerate(chars)}

def Encode(text: str) -> list[int]:
    return [(encoder[c] if (list(encoder.keys()).count(c) > 0) else encoder[" "]) for c in text]

def Decode(tokens: list[int]) -> str:
    return "".join([(decoder[t] if (list(decoder.keys()).count(t) > 0) else " ") for t in tokens])

# Create training tensor and variables
train_data_tensor = torch.tensor(Encode(train_data_full), dtype = torch.long)
n = int(len(train_data_tensor) * 0.9)
train_data_tensor_2 = train_data_tensor[:n]
val_data_tensor = train_data_tensor[n:]
block_size = 24
batch_size = 12
epochs = cfg.current_data.tf_epochs
max_length = 25
eval_interval = 150
learning_rate = 1e-3
move_to_gpu = torch.cuda.is_available() and cfg.current_data.use_gpu_if_available and cfg.current_data.move_to_gpu.__contains__("7")
device = torch.device("cuda" if move_to_gpu else "cpu")
eval_iters = 200
n_embed = 132 * 4
n_layer = 6
n_head = 24
dropout = 0.2

# Prepare training
def __get_batch__(split) -> tuple[torch.Tensor, torch.Tensor]:
    data = train_data_tensor_2 if (split == "train") else val_data_tensor
    ix = torch.randint(len(data) - block_size, (batch_size,))
    x = torch.stack([data[i:i + block_size] for i in ix])
    y = torch.stack([data[i + 1:i + block_size + 1] for i in ix])
    x, y = (x.to(device), y.to(device))

    return (x, y)

# Language model creation
class Head(nn.Module):
    def __init__(self, head_size) -> None:
        super().__init__()

        self.key = nn.Linear(n_embed, head_size, bias = False)
        self.query = nn.Linear(n_embed, head_size, bias = False)
        self.value = nn.Linear(n_embed, head_size, bias = False)

        self.register_buffer("tril", torch.tril(torch.ones(block_size, block_size)))
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x) -> torch.Tensor:
        _, T, C = x.shape
        k = self.key.forward(x)
        q = self.query.forward(x)
        wei = q @ k.transpose(-2, -1) * C ** -0.5
        wei = wei.masked_fill(self.tril[:T, :T] == 0, float("-inf"))
        wei = nn.functional.softmax(wei, dim = -1)
        wei = self.dropout.forward(wei)
        v = self.value.forward(x)

        return wei @ v

class MultiHeadAttention(nn.Module):
    def __init__(self, num_heads, head_size) -> None:
        super().__init__()

        self.heads = nn.ModuleList([Head(head_size) for _ in range(num_heads)])
        self.projection = nn.Linear(n_embed, n_embed)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x) -> torch.Tensor:
        out = torch.cat([h.forward(x) for h in self.heads], dim = -1)
        out = self.dropout.forward(self.projection.forward(out))

        return out

class FeedForward(nn.Module):
    def __init__(self, n_embed) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_embed, n_embed * 4),
            nn.ReLU(),
            nn.Linear(n_embed * 4, n_embed),
            nn.Dropout(dropout)
        )
    
    def forward(self, x) -> torch.Tensor:
        return self.net.forward(x)

class Block(nn.Module):
    def __init__(self, n_embed, n_head) -> None:
        super().__init__()

        head_size = n_embed // n_head
        self.sa = MultiHeadAttention(n_head, head_size)
        self.feed_forward = FeedForward(n_embed)
        self.layernorm1 = nn.LayerNorm(n_embed)
        self.layernorm2 = nn.LayerNorm(n_embed)
    
    def forward(self, x) -> torch.Tensor:
        x = x + self.sa.forward(self.layernorm1.forward(x))
        x = x + self.feed_forward.forward(self.layernorm2.forward(x))

        return x

class LanguageModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()

        self.token_embedding_table = nn.Embedding(vocab_size, n_embed)
        self.position_embedding_table = nn.Embedding(block_size, n_embed)
        self.blocks = nn.Sequential(*[Block(n_embed, n_head) for _ in range(n_layer)])
        self.ln_f = nn.LayerNorm(n_embed)
        self.lm_head = nn.Linear(n_embed, vocab_size)
    
    def forward(self, idx, targets = None) -> tuple[torch.Tensor, torch.Tensor]:
        B, T = idx.shape
        token_emb = self.token_embedding_table.forward(idx)
        pos_emb = self.position_embedding_table.forward(torch.arange(T, device = device))
        x = token_emb + pos_emb
        x = self.blocks.forward(x)
        logits = self.lm_head.forward(x)
        
        if (targets == None):
            loss = -1
        else:
            B, T, C = logits.shape
            logits = logits.view(B * T, C)
            targets = targets.view(B * T)
            loss = nn.functional.cross_entropy(logits, targets)

        return (logits, loss)

    def generate(self, idx, max_new_tokens) -> torch.Tensor:
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -block_size:]
            logits, _ = self.forward(idx_cond)
            logits = logits[:, -1, :]
            probs = nn.functional.softmax(logits, dim = -1)
            idx_next = torch.multinomial(probs, num_samples = 1)
            idx = torch.cat((idx, idx_next), dim = 1)
        
        return idx

@torch.no_grad()
def __estimate_loss__(model: LanguageModel):
    out = {}
    model.eval()

    for split in ["train", "val"]:
        losses = torch.zeros(eval_iters)

        for k in range(eval_iters):
            X, Y = __get_batch__(split)
            logits, loss = model.forward(X, Y)
            losses[k] = loss.item()
        
        out[split] = losses.mean()
    
    model.train()
    return out

# Train model
model: LanguageModel = LanguageModel().to(device)
optimizer = torch.optim.AdamW(model.parameters(), lr = learning_rate)

def TrainModel(model_name: str = "pt_model") -> None:
    global model, model_loaded

    if (model_loaded):
        return
    
    if (os.path.exists(model_name + ".pth")):
        try:
            model.load_state_dict(torch.load(model_name + ".pth"))
        except Exception as e:
            print(str(e))
    else:
        for iter in range(epochs):
            if (iter % eval_interval == 0):
                losses = __estimate_loss__(model)
                tl = float(losses["train"].item())
                vl = float(losses["val"].item())

                print("Epoch #" + str(iter) + ", train loss: " + str(tl) + ", val loss: " + str(vl) + "." + "\nTraining...")

            xb, yb = __get_batch__("train")
            _, loss = model.forward(xb, yb)

            optimizer.zero_grad(set_to_none = True)
            loss.backward()
            optimizer.step()

            #print("Epoch #" + str(iter + 1) + ", loss: " + str(loss) + ".")
    
    model_loaded = True

def SaveModel(model_name: str = "pt_model") -> None:
    torch.save(model.state_dict(), model_name + ".pth")

def GenerateResponse(prompt: str) -> str:
    encoded_prompt = Encode(prompt)
    encoded_prompt = torch.tensor(encoded_prompt, dtype = torch.long, device = device).unsqueeze(0)
    response = model.generate(encoded_prompt, max_new_tokens = max_length)[0].tolist()
    response = Decode(response)

    return response

"""try:
    TrainModel()
    SaveModel()

    while True:
        p = input("You: ")
        r = GenerateResponse(p)

        print("AI: " + r)
except Exception as ex:
    print("Error training model: " + str(ex))"""