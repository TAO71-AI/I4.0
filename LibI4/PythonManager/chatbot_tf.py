import tensorflow as tf
import numpy as np
import os
import ai_math_handler as mh
import ai_read_file as rf
import ai_config as cfg

# Other vars
allow_args = True
epochs = cfg.current_data.tf_epochs

model_loaded = False

# Prepare data
data_file = "tf_train_data_es.txt"
data = rf.read_vars_from_file(data_file, "SQ", "EQ", "SR", "ER")
data_i = [mh.number_to_str(i) for i in data]
data_o = [data[i] for i in data]

tokenizer = tf.keras.preprocessing.text.Tokenizer()
tokenizer.fit_on_texts(data_i)
word_index = tokenizer.word_index
sequences = tokenizer.texts_to_sequences(data_i)
ai_data = tf.keras.preprocessing.sequence.pad_sequences(sequences)

# Create model
model = tf.keras.Sequential()
model.add(tf.keras.layers.Embedding(len(word_index) + 1, 128))
model.add(tf.keras.layers.LSTM(128))
model.add(tf.keras.layers.Dense(len(data_o), activation = "softmax"))

# Compile model
model.compile(optimizer = "adam", loss = "categorical_crossentropy", metrics = ["accuracy"])

# Train model
labels = tf.keras.utils.to_categorical(np.arange(len(data_o)), len(data_o))

def train_model(model_name: str = "tf_model") -> None:
    global model_loaded, model

    if (model_loaded):
        return
    
    if (not os.path.exists(model_name)):
        model.fit(ai_data, labels, epochs = epochs)
    else:
        model = tf.keras.models.load_model(model_name)
    
    model_loaded = True

# Evaluate model
test_loss, test_acc = model.evaluate(ai_data, labels)

# Do predictions
def get_ai_response(input_data: str) -> str:
    global model
    global tokenizer
    global data_o

    try:
        sequence = tokenizer.texts_to_sequences([mh.number_to_str(input_data)])
        ai_data = tf.keras.preprocessing.sequence.pad_sequences(sequence)
        prediction = model.predict(ai_data)
        response_index = np.argmax(prediction)

        return data_o[response_index]
    except:
        return "ERROR."

def save_model(name: str = "tf_model") -> None:
    model.save(name)