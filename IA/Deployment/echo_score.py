import json
import numpy as np
import os
import tensorflow as tf
from tensorflow.keras.preprocessing.image import load_img
import pywt
import matplotlib.pyplot as plt

def init():
    global tf_model
    # the name of the folder in which to look for tensorflow model files
    #tf_model = tf.saved_model.load('../var/azureml-app/azureml-models/heartCNN_VGG16_DV3/2/heartCNN_VGG16_DV3_v1.4.h5')
    model_root = os.getenv('AZUREML_MODEL_DIR')
     # the name of the folder in which to look for tensorflow model files
    tf_model_folder = 'model'    
    tf_model = tf.saved_model.load(os.path.join(model_root, tf_model_folder))

def run(data):
    dataRequest = json.loads(data)["data"]
    results = []
    resultData = {}

    #print(type(dataRequest))
    #print(dataRequest)
    
    if(len(dataRequest['listECG']) > 0):
        imageData = createNpArray(dataRequest['listECG'])
        for image in imageData:
            out = tf_model(image)
            y_hat = np.argmax(out, axis=1)
            ##result = predict.argmax()
            results.append(y_hat.tolist()[0])
        
        resultData['results'] = results
        return resultData
    else:
        return "Error en obtener datos"



def createNpArray(listECG):
    npArray =[]
    print('createNpArray inicio')
    for ecg in listECG:
        my_dpi = 96
        fig = plt.figure(figsize=(224/my_dpi, 224/my_dpi), dpi=my_dpi)
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        ax.set_axis_off()
        fig.add_axes(ax)
        plt.imshow(get_coef(ecg, 'morl'), cmap='jet', interpolation="bilinear")
        fig.savefig('imageECG_ACI.png', dpi=my_dpi)

        imagen= load_img('imageECG_ACI.png',color_mode='rgb',target_size=None,interpolation='bilinear')
        ##image= cv2.resize(image, (IMG_HEIGHT, IMG_WIDTH),interpolation = cv2.INTER_AREA)
        imagen = np.array(imagen)
        imagen = imagen.astype('float32')
        imagen /= 255 
        imagen = np.expand_dims(imagen, axis = 0)
        #fig.canvas.draw()
        #X = np.array(fig.canvas.renderer.buffer_rgba())
        #X = X[...,:3].shape
        npArray.append(imagen)
    return npArray

def get_coef(ecg, waveletname):
    fs = len(ecg)
    scales = range(1, fs)
    
    coef, freqs = pywt.cwt(ecg ,scales, waveletname)
    return abs(coef)
