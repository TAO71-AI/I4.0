from tensorflow import keras
import numpy as np
import os
import ai_read_file as rf
import ai_config as cfg

data_file_path: str = cfg.current_data.tf_data_file
epochs: int = cfg.current_data.tf_epochs

model_loaded = False

# Preprocessing
data: list[str] = rf.read_lines_from_file(cfg.current_data.tf_data_file)

# Tokenization
tokenizer = keras.preprocessing.text.Tokenizer()
tokenizer.fit_on_texts(data)
num_words = len(tokenizer.word_index) + 1

# Sequences
seqs = tokenizer.texts_to_sequences(data)

# Padding
max_sequence_length = max(len(sequence) for sequence in seqs)
padded_input_seqs = keras.preprocessing.sequence.pad_sequences(seqs, maxlen = max_sequence_length, padding = "post")
padded_output_seqs = keras.preprocessing.sequence.pad_sequences(seqs, maxlen = max_sequence_length, padding = "post")

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
def train_model(model_name: str = "tf_model") -> None:
    global model_loaded, model

    if (model_loaded):
        return

    if (not os.path.exists(model_name)):
        model.fit(padded_input_seqs, np.expand_dims(padded_output_seqs, -1), epochs = epochs)
    else:
        model = keras.models.load_model(model_name)

    model_loaded = True

def get_ai_response(prompt: str) -> str:
    prompt_seq = tokenizer.texts_to_sequences([prompt])
    padded_prompt = keras.preprocessing.sequence.pad_sequences(prompt_seq, maxlen = max_sequence_length, padding = "post")
    predicted_seq = model.predict(padded_prompt)[0]
    predicted_seq = np.argmax(predicted_seq, axis = -1)
    predicted_response = tokenizer.sequences_to_texts([predicted_seq])[0]

    return predicted_response

def save_model(name: str = "tf_model") -> None:
    model.save(name)