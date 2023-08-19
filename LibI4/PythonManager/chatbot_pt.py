import torch
import torch.nn as nn
import torch.optim as optim
import random
import ai_read_file as rf
import ai_config as cfg

vocab = set()
data: dict[str, str] = rf.read_vars_from_file(cfg.current_data.tf_data_file, "SQ", "EQ", "SR", "ER")

for data_i, data_o in data.items():
    vocab.update(data_i.split())
    vocab.update(data_o.split())

vocab = list(vocab)

PAD_token = 0
SOS_token = 1
EOS_token = 2

vocab.append("<UNK>")
vocab.append("<PAD>")
vocab.append("<SOS>")
vocab.append("<EOS>")

word2index = {word: index for index, word in enumerate(vocab)}
index2word = {index: word for index, word in enumerate(vocab)}

def indexes_from_sentence(sentence: str):
    indexes = []

    for word in sentence.split():
        if (word in word2index):
            indexes.append(word2index[word])
        else:
            indexes.append(word2index.get('<UNK>', word2index['<PAD>']))
    
    return indexes

def sentence_from_indexes(indexes: set[int]):
    return " ".join(vocab[index] for index in indexes)

def random_training_sample():
    data_i, data_o = random.choice(list(data.items()))
    return data_i, data_o

class LSTMGenerator(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(LSTMGenerator, self).__init__()

        self.hidden_size = hidden_size
        self.embedding = nn.Embedding(input_size, hidden_size)
        self.lstm = nn.LSTM(hidden_size, hidden_size)
        self.out = nn.Linear(hidden_size, output_size)
    
    def forward(self, input, hidden):
        embedded = self.embedding(input).view(1, 1, -1)
        output, hidden = self.lstm(embedded, hidden)
        output = self.out(output[0])

        return output, hidden
    
    def init_hidden(self):
        return (torch.zeros(1, 1, self.hidden_size), torch.zeros(1, 1, self.hidden_size))

def train(input_tensor, target_tensor, model, optimizer, criterion):
    hidden = model.init_hidden()
    optimizer.zero_grad()
    input_length = input_tensor.size(0)
    target_length = target_tensor.size(0)
    loss = 0

    for i in range(input_length):
        output, hidden = model(input_tensor[i], hidden)
    
    target_tensor = target_tensor.view(target_length, 1)

    for i in range(target_length):
        output, hidden = model(target_tensor[i], hidden)
        loss += criterion(output, target_tensor[i])
    
    loss.backward()
    optimizer.step()

    return loss.item() / target_length

input_size = len(vocab)
hidden_size = 256
output_size = len(vocab)
learning_rate = 0.01
n_epochs = 1500

model = LSTMGenerator(input_size, hidden_size, output_size)
criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(model.parameters(), lr = learning_rate)

for epoch in range(1, n_epochs + 1):
    data_i, data_o = random_training_sample()
    input_tensor = torch.tensor(indexes_from_sentence(data_i), dtype = torch.long)
    target_tensor = torch.tensor(indexes_from_sentence(data_o), dtype = torch.long)
    loss = train(input_tensor, target_tensor, model, optimizer, criterion)

    print("Epoch " + str(epoch) + ", Loss: " + str(loss))
    
print("Training complete.")

def generate_response(data_i, model):
    with torch.no_grad():
        input_tensor = torch.tensor(indexes_from_sentence(data_i), dtype = torch.long)
        hidden = model.init_hidden()
        output_response = []

        for i in range(input_tensor.size(0)):
            output, hidden = model(input_tensor[i], hidden)
        
        SOS_token_tensor = torch.tensor(SOS_token, dtype = torch.long)
        output_response.append(SOS_token_tensor)

        for i in range(20):
            output, hidden = model(output_response[-1], hidden)
            topv, topi = output.topk(1)

            if (topi.item() == EOS_token):
                break
            else:
                output_response.append(topi.squeeze().detach())
        
        response = sentence_from_indexes(output_response)
        return response

print(generate_response("Hello!", model))