import sys
import numpy as np
from keras.preprocessing.text import Tokenizer
from keras.preprocessing import sequence
from sklearn.preprocessing import LabelEncoder
from keras.models import model_from_json

import pickle
import time
import gzip

def predict_category(query):
    le = pickle.load( open( './module/model/LabelEncoder', "rb" ) )

    # Load LSTM Classification Model
    json_file = open('./module/model/LSTM_classifier_binary.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    model = model_from_json(loaded_model_json)
    model.compile(loss='binary_crossentropy',
				  optimizer='adam',
				  metrics=['accuracy'])
    model.load_weights("./module/model/LSTM_classifier_binary_weights.h5")
    with open('./module/model/LSTM_classifier_binary.pickle', 'rb') as handle:
        tokenizer = pickle.load(handle)

    t = tokenizer.texts_to_sequences(query)
    t = sequence.pad_sequences(t, maxlen=50)
    prediction = model.predict_classes(np.array(t))
    predicted_category = le.inverse_transform(prediction)
    #print("Sentence: ",query," / Predict: ",predicted_category)

    return predicted_category
