from tensorflow import keras
import numpy as np
import ai_read_file as rf
import ai_config as cfg

data_file_path: str = cfg.ReadConfig().tf_data_file
epochs: int = cfg.ReadConfig().tf_epochs

# Preprocessing
data: dict = rf.read_vars_from_file(data_file_path, "SQ", "EQ", "SR", "ER")
inputs = list(data.keys())
outputs = list(data.values())

# Tokenization
tokenizer = keras.preprocessing.text.Tokenizer()
tokenizer.fit_on_texts(inputs + outputs)
num_words = len(tokenizer.word_index) + 1

# Sequences
input_seqs = tokenizer.texts_to_sequences(inputs)
output_seqs = tokenizer.texts_to_sequences(outputs)

# Padding
max_sequence_length = max(max(len(sequence) for sequence in input_seqs), max(len(sequence) for sequence in output_seqs))
padded_input_seqs = keras.preprocessing.sequence.pad_sequences(input_seqs, maxlen = max_sequence_length, padding = "post")
padded_output_seqs = keras.preprocessing.sequence.pad_sequences(output_seqs, maxlen = max_sequence_length, padding = "post")

# Create model
model = keras.models.Sequential()

model.add(keras.layers.Embedding(num_words, 128, input_length = max_sequence_length, mask_zero = True))
model.add(keras.layers.LSTM(128))
model.add(keras.layers.RepeatVector(max_sequence_length))
model.add(keras.layers.LSTM(128, return_sequences = True))
model.add(keras.layers.TimeDistributed(keras.layers.Dense(num_words, activation = "softmax")))

# Compile model
model.compile(optimizer = "adam", loss = "sparse_categorical_crossentropy")

# Functions
def train():
    model.fit(padded_input_seqs, np.expand_dims(padded_output_seqs, -1), epochs = epochs)

def get_ai_response(prompt: str):
    prompt_seq = tokenizer.texts_to_sequences([prompt])
    padded_prompt = keras.preprocessing.sequence.pad_sequences(prompt_seq, maxlen = max_sequence_length, padding = "post")
    predicted_seq = model.predict(padded_prompt)[0]
    predicted_seq = np.argmax(predicted_seq, axis = -1)
    predicted_response = tokenizer.sequences_to_texts([predicted_seq])[0]

    return predicted_response

train()