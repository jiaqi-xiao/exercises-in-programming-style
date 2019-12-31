from keras.models import Sequential
from keras.layers import Dense, LSTM, RepeatVector, TimeDistributed
from keras.losses import binary_crossentropy, categorical_crossentropy
from keras.optimizers import SGD
from keras. metrics import top_k_categorical_accuracy
from keras import backend as K
import numpy as np
import sys, os, string, random

characters = string.printable
char_indices = dict((c, i) for i, c in enumerate(characters))
indices_char = dict((i, c) for i, c in enumerate(characters))

INPUT_VOCAB_SIZE = len(characters)
BATCH_SIZE = 200
HIDDEN_SIZE = 128
N_LAYERS = 1
TIME_STEPS = 3

def encode_one_hot(line):
    remain = len(line) % TIME_STEPS
    if remain != 0:
        line = line + ' ' * (TIME_STEPS-remain)
    x = np.zeros((len(line), INPUT_VOCAB_SIZE))
    for i, c in enumerate(line):
        index = char_indices[c] if c in characters else char_indices[' ']
        x[i][index] = 1 
    return np.reshape(x, ( (int)(len(line) / TIME_STEPS), TIME_STEPS, INPUT_VOCAB_SIZE ) )

def decode_one_hot(y):
    x = np.reshape(y, (y.shape[0]*y.shape[1], INPUT_VOCAB_SIZE))
    s = []
    for onehot in x:
        one_index = np.argmax(onehot) 
        s.append(indices_char[one_index]) 
    return ''.join(s)
    
def input_generator(nsamples):
    def generate_line():
        inline = []; outline = []
        for _ in range(nsamples):
            c = random.choice(characters) 
            expected = c.lower() if c in string.ascii_letters else ' ' 
            inline.append(c); outline.append(expected)
        for i in range(nsamples):
            if outline[i] == ' ': continue
            if i > 0 and i < nsamples-1:
                if outline[i-1] == ' ' and outline[i+1] == ' ':
                    outline[i] = ' '
            if (i == 0 and outline[1] == ' ') or (i == nsamples-1 and outline[nsamples-2] == ' '):
                outline[i] = ' '
        return ''.join(inline), ''.join(outline)

    while True:
        input_data, expected = generate_line()
        #print("Input :", input_data)
        #print("Output:", expected)
        data_in = encode_one_hot(input_data)
        data_out = encode_one_hot(expected)
        yield data_in, data_out

def train(model):
    model.compile(loss='categorical_crossentropy',
                  optimizer='adam',
                  metrics=['accuracy'])
    input_gen = input_generator(BATCH_SIZE)
    validation_gen = input_generator(BATCH_SIZE)
    model.fit_generator(input_gen,
                epochs = 200, workers=1,
                steps_per_epoch = 50,
                validation_data = validation_gen,
                validation_steps = 10)

def build_model():
    model = Sequential()
    r_layer = LSTM(HIDDEN_SIZE, input_shape=(None, INPUT_VOCAB_SIZE))
    model.add(r_layer)
    model.add(RepeatVector(TIME_STEPS))
    for _ in range(N_LAYERS):
        model.add(LSTM(HIDDEN_SIZE, return_sequences=True))
    model.add(TimeDistributed(Dense(INPUT_VOCAB_SIZE, activation='softmax')))
    return model

model = build_model()
model.summary()
train(model)

input("Network has been trained. Press <Enter> to run program.")
with open(sys.argv[1]) as f:
    for line in f:
        if line.isspace(): continue
        batch = encode_one_hot(line)
        preds = model.predict(batch)
        normal = decode_one_hot(preds)
        print(normal)