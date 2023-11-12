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
tokenizer: tf.keras.preprocessing.text.Tokenizer = None
data: list[str] = []
model: tf.keras.Sequential = None

def prepare() -> tuple:
    # Prepare data
    data_file = "tf_train_data_es.txt"
    data = rf.read_lines_from_file(data_file)
    data = [mh.number_to_str(i) for i in data]

    tokenizer = tf.keras.preprocessing.text.Tokenizer()
    tokenizer.fit_on_texts(data)
    word_index = tokenizer.word_index
    sequences = tokenizer.texts_to_sequences(data)
    ai_data = tf.keras.preprocessing.sequence.pad_sequences(sequences)

    # Create model
    model = tf.keras.Sequential()
    model.add(tf.keras.layers.Embedding(len(word_index) + 1, 128))
    model.add(tf.keras.layers.LSTM(128))
    model.add(tf.keras.layers.Dense(len(data), activation = "softmax"))

    # Compile model
    model.compile(optimizer = "adam", loss = "categorical_crossentropy", metrics = ["accuracy"])

    # Train model
    labels = tf.keras.utils.to_categorical(np.arange(len(data)), len(data))

    # Evaluate model
    test_loss, test_acc = model.evaluate(ai_data, labels)
    return ai_data, labels, test_loss, test_acc

def train_model(model_name: str = "tf_model") -> None:
    global model_loaded, model
    ai_data, labels = prepare()

    if (model_loaded):
        return
    
    if (not os.path.exists(model_name)):
        model.fit(ai_data, labels, epochs = epochs)
    else:
        model = tf.keras.models.load_model(model_name)
    
    model_loaded = True

# Do predictions
def get_ai_response(input_data: str) -> str:
    global model
    global tokenizer
    global data

    try:
        sequence = tokenizer.texts_to_sequences([mh.number_to_str(input_data)])
        ai_data = tf.keras.preprocessing.sequence.pad_sequences(sequence)
        prediction = model.predict(ai_data)
        response_index = np.argmax(prediction)

        return data[response_index]
    except:
        return "ERROR."

def save_model(name: str = "tf_model") -> None:
    model.save(name)