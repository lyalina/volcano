# -*- coding: utf-8 -*-
"""volcano3-Classification NN

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1A89hZG99dQm9f8l49lznC2fwHUDJjsVP

# Классификация извержения вулкана с помощью нейронных сетей

# 1. Problem Statement
Необходимо по снимкам с веб-камеры определять происходит в данный момент извержение вулкана или нет. 
Если да, то какая активность зафиксирована.
Если видимости нет, то почему - ночь, облачно, туман.

## Libraries and Functions
"""

from google.colab import drive
drive.mount('/content/drive')

# Commented out IPython magic to ensure Python compatibility.
# Common libraries
import os
import random
from glob import glob
from imutils import paths
from os import path
import re

# Ignore warnings
import warnings
warnings.filterwarnings('ignore')

# Handle table-like data and matrices
import numpy as np
import pandas as pd

# Visualisation
import cv2
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.pylab as pylab

# Configure visualisations
# %matplotlib inline
mpl.style.use('ggplot')
plt.rcParams["axes.grid"] = False

# Modeling Algorithms
import tensorflow as tf
from keras.utils import to_categorical
from keras.models import load_model
from sklearn.metrics import mean_squared_error, accuracy_score, classification_report, recall_score, f1_score, precision_score
from sklearn.metrics import plot_roc_curve 
from sklearn.metrics import confusion_matrix 

print(tf.__version__)
print(tf.executing_eagerly())

project_path = '/content/drive/MyDrive/ML/Volcano/'
IMG_SIZE = (256, 256)
class_status = {0: 'alert', 
               1: 'normal'}

class_pillar = {0: '-', 
               1: 'pillar'}

class_lava = {0: '-', 
              1: 'lava'}

# Загрузка изображения и приведение к общему размеру 
def load_image(path, target_size=IMG_SIZE):
    image = cv2.imread(path)[...,::-1]
    image = cv2.resize(image, target_size)
    return image  

# Обработка изображения - размерность не меняется
def gradient_image(src):
    image = cv2.cvtColor(src, cv2.COLOR_BGR2RGB)
    image = cv2.GaussianBlur(image, (3, 3), 0)
    ##laplacian = cv2.Laplacian(image,cv2.CV_64F)
    sobelx = cv2.Sobel(image,cv2.CV_64F,1,0,ksize=5)
    sobely = cv2.Sobel(image,cv2.CV_64F,0,1,ksize=5)
    abs_grad_x = cv2.convertScaleAbs(sobelx)
    abs_grad_y = cv2.convertScaleAbs(sobely)    
    image = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0) 
    
    return image 

# Вывод заданного количества изображений из указанной папки    # не используется?
def show_images(imagePaths, nrows = 1, ncols = 5):
  fig = plt.figure(figsize=(16, 8))
  for i, path in enumerate(imagePaths, 1):
      subplot = fig.add_subplot(nrows, ncols, i)
      subplot.set_title('%s' % path.split('/')[-2])
      img = cv2.imread(path)[...,::-1]
      img = cv2.resize(img, IMG_SIZE)
      plt.axis('off')
      plt.imshow(img)


# Вывод заданного количества изображений для генератора
def show_images_gen(generator, nrows = 1, ncols = 5):
  fig = plt.figure(figsize=(16, 8))
  for i, path in enumerate(generator[0][0:nrows*ncols],1) :
      subplot = fig.add_subplot(nrows, ncols, i)
      subplot.set_title(class_status.get(generator[1][i]))
      img = generator[0][i]
      plt.axis('off')
      plt.imshow(img)

# Вывод заданного количества изображений для генератора классов
def show_images_gen_class(generator, nrows = 1, ncols = 5):
  fig = plt.figure(figsize=(16, 8))
  for i, path in enumerate(generator[0][0:nrows*ncols],1) :
      subplot = fig.add_subplot(nrows, ncols, i)
      title = 'pillar:%s lava:%s \nclear:%s cloud:%s mist:%s' % (class_pillar.get(generator[1][i][0]), class_lava.get(generator[1][i][1]),  generator[1][i][2],generator[1][i][3],generator[1][i][4])
      subplot.set_title(title, fontsize=8)
      img = generator[0][i]
      plt.axis('off')
      plt.imshow(img)


# Вывод изображения заданного количества картинок из пердсказания модели: класс и вероятность отнесения к классу
def show_images_predict(test_files,y_pred, nrows = 1, ncols = 5):
    n_img = nrows*ncols
    fig = plt.figure(figsize=(20, 6))
    for i, (path, score) in enumerate(zip(test_files[0:n_img], y_pred[0:n_img]), 1):
        title = '%s: %s' % (class_status.get(int(round(score[0]))), np.round(score[0],3))
        subplot = fig.add_subplot(nrows, ncols, i)
        subplot.set_title(title, fontsize=8)
        img = cv2.imread(path)[...,::-1]
        img = cv2.resize(img, IMG_SIZE)
        subplot.imshow(img)
        plt.axis('off')
        
# Вывод изображения заданного количества картинок из пердсказания модели: класс и вероятность отнесения к классу
def show_images_predict_class(test_files,y_pred, nrows = 1, ncols = 5):
    n_img = nrows*ncols
    fig = plt.figure(figsize=(25, 10))
    for i, (path, score) in enumerate(zip(test_files[0:n_img], y_pred[0:n_img]), 1):
        title = 'pillar:%s lava:%s \nclear:%s cloud:%s mist:%s' % (np.round(score[0],3),np.round(score[1],3),  np.round(score[2],3), np.round(score[3],3), np.round(score[4],3))
        subplot = fig.add_subplot(nrows, ncols, i)
        subplot.set_title(title, fontsize=8)
        img = cv2.imread(path)[...,::-1]
        img = cv2.resize(img, IMG_SIZE)
        subplot.imshow(img)
        plt.axis('off')


def plot_model_history(model_history):
      # Getting the accuracy and loss
      acc = model_history.history['accuracy']
      val_acc = model_history.history['val_accuracy']
      loss = model_history.history['loss']
      val_loss = model_history.history['val_loss']
      # Plotting the accuracy
      epochs = range(len(acc))

      fig = plt.figure(figsize=(16, 6))
      subplot = fig.add_subplot(1, 2, 1)
      subplot.set_title('accuracy')
      plt.plot(epochs, acc, '-o', label='Training accuracy')
      plt.plot(epochs, val_acc, '-', label='Validation accuracy')
      plt.title('Training and validation accuracy')
      plt.grid(linestyle='--')
      plt.legend()

      subplot = fig.add_subplot(1, 2, 2)
      subplot.set_title('loss')
      plt.plot(epochs, loss, '-o', label='Training Loss' )
      plt.plot(epochs, val_loss, '-', label='Validation Loss')
      plt.title('Training and validation loss')
      plt.legend()
      plt.grid(linestyle='--')
      plt.show()

# функция-генератор загрузки обучающих данных с диска      не используется больше
def fit_generator(files, batch_size=24):   #  долго обучается 1 
    batch_size = min(batch_size, len(files))
    while True:
        random.shuffle(files)
        for k in range(len(files) // batch_size):
            i = k * batch_size
            j = i + batch_size
            if j > len(files):
                j = - j % len(files)
            x = np.array([load_image(path) for path in files[i:j]])
            y = np.array([1 if  path.split(os.path.sep)[-2] == 'normal' else 0
                          for path in files[i:j]])
            yield (x, y)

# функция-генератор загрузки обучающих данных с диска
def fit_generator_binary_class(files, class_name='status', batch_size=24):   
    batch_size = min(batch_size, len(files))
    while True:
        random.shuffle(files)
        for k in range(len(files) // batch_size):
            i = k * batch_size
            j = i + batch_size
            if j > len(files):
                j = - j % len(files)
            x = np.array([load_image(path) for path in files[i:j]])
            y_status = np.array([1 if  path.split(os.path.sep)[-2] == 'normal' else 0    
                          for path in files[i:j]])

            y_pillar, y_lava, y_activity = encode(files[i:j])

            if class_name == 'status': y = y_status
            if class_name == 'pillar': y = np.array(y_pillar)
            if class_name == 'lava':   y = np.array(y_lava)

            yield (x, y)

# функция-генератор загрузки обучающих данных с диска
def fit_generator_classes(files, batch_size=24):   
    batch_size = min(batch_size, len(files))
    while True:
        random.shuffle(files)
        for k in range(len(files) // batch_size):
            i = k * batch_size
            j = i + batch_size
            if j > len(files):
                j = - j % len(files)
            x = np.array([load_image(path) for path in files[i:j]])
            y = np.array([1 if  path.split(os.path.sep)[-2] == 'normal' else 0   
                          for path in files[i:j]])

            y_pillar, y_lava, y_activity = encode(files[i:j])

            yield (x, np.array(y_activity))

# функция-генератор загрузки тестовых изображений с диска
def predict_generator(files):
    while True:
        for path in files:
            yield np.array([load_image(path)])

def encode(files_path):
    y_visible = []   # класс видимость категориальный признак (mist, cloud,clear)   
    y_pillar = []    # класс тип активности: 1 - парогазовый столб
    y_lava = []      # класс тип активности: 1 - лава
    y_activity = []  # обощенные признаки всех классов  - pillar	lava	visible__clear	visible__cloud	visible__mist
    for path in files_path:
              result_vis = re.match(r'[a-zA-Z]+', path.split(os.path.sep)[-1])  
              y_visible.append( result_vis.group(0))

              result = re.split(r'\+', path.split(os.path.sep)[-1])
              if result[1] == 'pillar': y_pillar.append(1) 
              else: y_pillar.append(0)
              if result[2] == 'lava': y_lava.append(1) 
              else: y_lava.append(0) 

              y_activity = pd.DataFrame()
              y_activity['pillar'] = y_pillar
              y_activity['lava'] = y_lava
              y_activity = y_activity.join(pd.get_dummies(y_visible, prefix='visible_'))
              y_activity = np.array(y_activity)
              
    return y_pillar, y_lava, y_activity

def plot_confusion_matrix(df_confusion, title='Confusion matrix', cmap=plt.cm.gray_r):
    plt.matshow(df_confusion, cmap='Blues') # imshow
    #plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(df_confusion.columns))
    plt.xticks(tick_marks, df_confusion.columns, rotation=45)
    plt.yticks(tick_marks, df_confusion.index)
    plt.ylabel(df_confusion.index.name)
    plt.xlabel(df_confusion.columns.name)

"""# 2. Data Understanding

Набор данных - фотографии вуканов, разделенные на несколько классов:

•	класс состояние: 

'**alert**' (0) -  на фото зафиксирована любая активность на вулкане: парогазовый столб, взрыв, потоки лавы, 

'**normal**' (1) - нормальное состояние, никакой активности вулкана не отмечается, либо видимость не позволяет определить более точно. 

•	класс видимость: 

*	**clear** – ясно 
*	**cloud** – облачно 
*	**mist** – туман, сумерки, плохая видимость

•	класс выбросов - **парогазовый столб** (шлейф): 

* 0 / 1 – не определено / определено наличие парогазовых выбросов

•	класс выбросов -  **лава**:

*	 0 / 1 - не определено / определено наличие лавовых потоков.

### 2.1 Загрузка данных

Подготовим три датасета. 
Датасеты для обучения и вализации разбиты на классы. Класс соответствует названию папки.
Датасет для теста не разбит по классам.
"""

# данные читаем функцией-генератором

imagePaths_train = sorted(list(paths.list_images(path.join(project_path,'data/processed/train'))))
imagePaths_validation = sorted(list(paths.list_images(path.join(project_path,'data/processed/test'))))
imagePaths_test = sorted(list(paths.list_images(path.join(project_path,'data/raw/img'))))


random.shuffle(imagePaths_train)  # перемешиваем обучающую выборку
random.shuffle(imagePaths_validation)

# бинарная классификация
validation_ds = fit_generator_binary_class(imagePaths_train, 'status')
train_ds = fit_generator_binary_class(imagePaths_validation, 'status')  
test_ds = predict_generator(imagePaths_test)

# множественная классификация
train_ds_classes = fit_generator_classes(imagePaths_train)  
validation_ds_classes = fit_generator_classes(imagePaths_validation)

show_images_gen(next(train_ds),1,5)

show_images_gen(next(validation_ds),1,5)

plt.imshow(next(test_ds)[0])

"""### 2.2 Анализ данных

Для анализа данных пробуем использовать различные фильтры, переводим в различные цветовые схемы. 
"""

src = cv2.GaussianBlur(next(train_ds)[0][0], (3, 3), 0)
laplacian = cv2.Laplacian(src,cv2.CV_64F)
src = cv2.cvtColor(src, cv2.COLOR_BGR2HSV)  
sobelx = cv2.Sobel(src,cv2.CV_64F,1,0,ksize=3)
sobely = cv2.Sobel(src,cv2.CV_64F,0,1,ksize=3)
abs_grad_x = cv2.convertScaleAbs(sobelx)
abs_grad_y = cv2.convertScaleAbs(sobely)
    
grad = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0) 
grad = cv2.cvtColor(grad, cv2.COLOR_HSV2BGR)  
plt.imshow(grad)

grad.shape

"""#  3.  Data Preparation

В данном разделе проводится анализ использования нейронных сетей без дополнительных преобразований изображений, кроме изменения размера.

# 4. Modeling 

С помощью нейронных сетей построим модели бинарной и множественной классификации для определения состояния вулкана. 
С помощью бинарной определим есть активность или нет. 
С помощью множественной будем определять вероятность каждого из возможных состояний вулкана и условий съемки.
Для обеих задач классификации будем использовать предобученные сеть ResNet50 и VGG16 и веса imagenet.

## 4.1 Бинарная классификация
Для начала определим зафиксирована или нет активность на вулкане, т.е. решим задачу бинарной классификации.

Без весов
"""

input_img1 = tf.keras.layers.Input(shape=(256, 256, 3))


x1 = tf.keras.layers.Conv2D(128, (3, 3), padding = 'same', activation = 'relu')(input_img1)
x1 = tf.keras.layers.Conv2D(128, (3, 3), padding = 'same', activation = 'relu')(x1)
x1 = tf.keras.layers.GaussianNoise(3)(x1)
x1 = tf.keras.layers.Conv2D(128, (3, 3), padding = 'same', activation = 'relu')(x1)
x1 = tf.keras.layers.Conv2D(128, (3, 3), padding = 'same', activation = 'relu')(x1)
x1 = tf.keras.layers.MaxPooling2D((2, 2))(x1)
x1 = tf.keras.layers.Dropout(.2, input_shape=(2,))(x1)
x1 = tf.keras.layers.BatchNormalization()(x1)
x1 = tf.keras.layers.Conv2D(64, (3, 3), padding = 'same', activation = 'relu')(x1)
x1 = tf.keras.layers.Conv2D(64, (3, 3), padding = 'same', activation = 'relu')(x1)
x1 = tf.keras.layers.BatchNormalization()(x1)
x1 = tf.keras.layers.Conv2D(64, (3, 3), padding = 'same', activation = 'relu')(x1)
x1 = tf.keras.layers.Conv2D(64, (3, 3), padding = 'same', activation = 'relu')(x1)
x1 = tf.keras.layers.Dropout(.2, input_shape=(2,))(x1)

x1 = tf.keras.layers.BatchNormalization()(x1)

x1 = tf.keras.layers.Flatten()(x1)

x_class1 = tf.keras.layers.Dense(1,  
                          activation='sigmoid',   
                          kernel_regularizer=tf.keras.regularizers.l1(1e-4))(x1)

model = tf.keras.Model([input_img1], [x_class1])
model.compile(optimizer='rmsprop', loss=['mse', 'binary_crossentropy'], metrics=['accuracy'])
model.summary()

es_callback = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=3)

history_model =  model.fit(train_ds, epochs=30, steps_per_epoch=80, validation_data=validation_ds, callbacks=[es_callback], validation_steps=1)

plot_model_history(history_model)

test_pred_model = model.predict(predict_generator(imagePaths_test), steps=len(imagePaths_test))
test_pred_model

show_images_predict(imagePaths_test,test_pred_model, 4,  10)

"""### ResNet50"""

base_model = tf.keras.applications.ResNet50(weights='imagenet', include_top=False, input_shape=(256, 256, 3), classes=2) 

for layer in base_model.layers:
    layer.trainable = False

x = base_model.layers[-5].output
x = tf.keras.layers.Conv2D(128, (3, 3), padding = 'same', activation = 'relu')(x)
x = tf.keras.layers.Conv2D(128, (3, 3), padding = 'same', activation = 'relu')(x)
x = tf.keras.layers.MaxPooling2D((2, 2))(x)
x = tf.keras.layers.Dropout(.2, input_shape=(2,))(x)
x = tf.keras.layers.Conv2D(64, (3, 3), padding = 'same', activation = 'relu')(x)
x = tf.keras.layers.Conv2D(64, (3, 3), padding = 'same', activation = 'relu')(x)
x = tf.keras.layers.MaxPooling2D((2, 2))(x)
x = tf.keras.layers.Dense(32, activation = 'relu')(x)
x = tf.keras.layers.Dense(32, activation = 'relu')(x)
x = tf.keras.layers.Flatten()(x)
x = tf.keras.layers.BatchNormalization()(x)
x = tf.keras.layers.Dense(1,  
                          activation='sigmoid',   
                          kernel_regularizer=tf.keras.regularizers.l1(1e-4))(x)

ResNet_model_status =  tf.keras.Model(inputs = base_model.input, outputs=x)

ResNet_model_status.compile(optimizer='adam', loss=['mse', 'binary_crossentropy'], metrics=['accuracy'])

ResNet_model_status.summary()

es_callback = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=3)

history_ResNet_model_status = ResNet_model_status.fit(train_ds, epochs=30, steps_per_epoch=80, callbacks=[es_callback], validation_data=validation_ds, validation_steps=2)

test_pred_ResNet_model_status = ResNet_model_status.predict(predict_generator(imagePaths_test), steps=len(imagePaths_test))
test_pred_ResNet_model_status

plot_model_history(history_ResNet_model_status)

show_images_predict(imagePaths_test,test_pred_ResNet_model_status, 4,  10)

ResNet_model_status.save(path.join(project_path,'models/resnet_model_status.h5'))

"""ResNet50 без дополнительных слоев"""

base_model = tf.keras.applications.ResNet50(weights='imagenet', include_top=False, input_shape=(256, 256, 3), classes=2) 

for layer in base_model.layers:
    layer.trainable = False


x = base_model.layers[-1].output

x = tf.keras.layers.Flatten()(x)
x = tf.keras.layers.BatchNormalization()(x)
x = tf.keras.layers.Dense(1, 
                          activation='sigmoid',    
                          kernel_regularizer=tf.keras.regularizers.l1(1e-4))(x)

ResNet_model =  tf.keras.Model(inputs = base_model.input, outputs=x)

ResNet_model.compile(optimizer='adam', loss=['mse', 'binary_crossentropy'], metrics=['accuracy'])

es_callback = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=3)

history_ResNet_model = ResNet_model.fit(train_ds, epochs=30, steps_per_epoch=80, callbacks=[es_callback], validation_data=validation_ds, validation_steps=2)

test_pred_ResNet_model = ResNet_model.predict(predict_generator(imagePaths_test), steps=len(imagePaths_test))
test_pred_ResNet_model

plot_model_history(history_ResNet_model)

show_images_predict(imagePaths_test,test_pred_ResNet_model, 4,  10)

"""### VGG19"""

base_model_VGG = tf.keras.applications.VGG19(weights='imagenet', include_top=False, input_shape=(256, 256, 3), classes=2) 

for layer in base_model.layers:
    layer.trainable = False

x = base_model_VGG.layers[-1].output

x = tf.keras.layers.Flatten()(x)
x = tf.keras.layers.BatchNormalization()(x)
x = tf.keras.layers.Dense(1,  
                          activation='sigmoid',   
                          kernel_regularizer=tf.keras.regularizers.l1(1e-4))(x)

VGG_model_status =  tf.keras.Model(inputs = base_model_VGG.input, outputs=x)

VGG_model_status.compile(optimizer='adam', loss=['mse', 'binary_crossentropy'], metrics=['accuracy'])
es_callback = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=3)

history_VGG = VGG_model_status.fit(train_ds, epochs=30, steps_per_epoch=80, callbacks=[es_callback], validation_data=validation_ds, validation_steps=2)

test_pred_VGG_model_status = VGG_model_status.predict(predict_generator(imagePaths_test), steps=len(imagePaths_test))
test_pred_VGG_model_status

plot_model_history(history_VGG)

show_images_predict(imagePaths_test,test_pred_VGG_model, 4,  10)

base_model_VGG = tf.keras.applications.VGG19(weights='imagenet', include_top=False, input_shape=(256, 256, 3), classes=2) 

for layer in base_model_VGG.layers:
    layer.trainable = False


x = base_model_VGG.layers[-5].output
x = tf.keras.layers.Conv2D(128, (3, 3), padding = 'same', activation = 'relu')(x)
x = tf.keras.layers.Conv2D(128, (3, 3), padding = 'same', activation = 'relu')(x)
x = tf.keras.layers.MaxPooling2D((2, 2))(x)
x = tf.keras.layers.Dropout(.2, input_shape=(2,))(x)

x = tf.keras.layers.Conv2D(64, (3, 3), padding = 'same', activation = 'relu')(x)
x = tf.keras.layers.Conv2D(64, (3, 3), padding = 'same', activation = 'relu')(x)
x = tf.keras.layers.MaxPooling2D((2, 2))(x)

x = tf.keras.layers.Dense(32, activation = 'relu')(x)
x = tf.keras.layers.Dense(32, activation = 'relu')(x)
x = tf.keras.layers.Flatten()(x)
x = tf.keras.layers.BatchNormalization()(x)

x = tf.keras.layers.Flatten()(x)
x = tf.keras.layers.BatchNormalization()(x)

x = tf.keras.layers.Dense(1,  
                          activation='sigmoid',  
                          kernel_regularizer=tf.keras.regularizers.l1(1e-4))(x)

VGG_model_status =  tf.keras.Model(inputs = base_model_VGG.input, outputs=x)

VGG_model_status.compile(optimizer='adam', loss=['mse', 'binary_crossentropy'], metrics=['accuracy'])
es_callback = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=3)

history_VGG_model_status = VGG_model_status.fit(train_ds, epochs=30, steps_per_epoch=80, callbacks=[es_callback], validation_data=validation_ds, validation_steps=2)

test_pred_VGG_model_status = VGG_model_status.predict(predict_generator(imagePaths_test), steps=len(imagePaths_test))
test_pred_VGG_model_status

show_images_predict(imagePaths_test,test_pred_VGG_model_status, 4,  10)

plot_model_history(history_VGG_model_status)

VGG_model_status.save(path.join(project_path,'models/VGG_model_status.h5'))

"""VGG19 без дополнительных слоев так же дает сходный результат. Но в спорной картинке это может быть хуже.

Самый лучший результат по метрикам loss и accuracy.Чувствительность низкая, на спорной картинке однозначно отнесено к классу(неверному)

## 4.2 Multiclass
"""

show_images_gen_class(next(train_ds_classes),1,5)

show_images_gen_class(next(validation_ds_classes),1,5)

plt.imshow(next(test_ds)[0])

"""### ResNet50 multiclass"""

base_model_ResNet = tf.keras.applications.ResNet50(weights='imagenet', include_top=False, input_shape=(256, 256, 3), classes=5) 

for layer in base_model_ResNet.layers:
    layer.trainable = False

x = base_model_ResNet.layers[-1].output

x = tf.keras.layers.Conv2D(128, (3, 3), padding = 'same', activation = 'relu')(x)
x = tf.keras.layers.Conv2D(128, (3, 3), padding = 'same', activation = 'relu')(x)
x = tf.keras.layers.MaxPooling2D((2, 2))(x)
x = tf.keras.layers.Dropout(.2, input_shape=(2,))(x)

x = tf.keras.layers.Conv2D(64, (3, 3), padding = 'same', activation = 'relu')(x)
x = tf.keras.layers.Conv2D(64, (3, 3), padding = 'same', activation = 'relu')(x)
x = tf.keras.layers.MaxPooling2D((2, 2))(x)

x = tf.keras.layers.BatchNormalization()(x)
x = tf.keras.layers.Flatten()(x)
x = tf.keras.layers.Dense(5,  
                          activation='softmax',   
                          kernel_regularizer=tf.keras.regularizers.l1(1e-4))(x)

ResNet_model_multiclass =  tf.keras.Model(inputs = base_model_ResNet.input, outputs=x)

ResNet_model_multiclass.compile(optimizer='adam', loss=['mse','categorical_crossentropy'], metrics=['accuracy'])

"""Так как классы не сбалансированы и объединены в одну модель добавим веса.  Значимость классов выбросов больше чем класса видимости.

Оценка качества только кросс энтропии дает большую погрешность, добавляем MSE.
"""

es_callback = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=3)

class_weights = {0: 1.5, 1: 3., 2: 0.2, 3: 0.3, 4: 0.8}

history_ResNet_model_multiclass = ResNet_model_multiclass.fit(train_ds, epochs=10, callbacks=[es_callback] , steps_per_epoch=10,  validation_data=validation_ds, validation_steps=3)

test_pred_ResNet_model_multiclass = ResNet_model_multiclass.predict(predict_generator(imagePaths_test), steps=len(imagePaths_test))
test_pred_ResNet_model_multiclass

plot_model_history(history_ResNet_model_multiclass)

show_images_predict_class(imagePaths_test,test_pred_ResNet_model_multiclass, 4, 10)

ResNet_model_multiclass.save(path.join(project_path,'models/resnet_multiclass_model.h5'))

"""### VGG multiclass"""

base_model_VGG = tf.keras.applications.VGG19(weights='imagenet', include_top=False, input_shape=(256, 256, 3), classes=5) 

for layer in base_model_VGG.layers:
    layer.trainable = False


x = base_model_VGG.layers[-5].output
x = tf.keras.layers.Conv2D(128, (3, 3), padding = 'same', activation = 'relu')(x)
x = tf.keras.layers.Conv2D(128, (3, 3), padding = 'same', activation = 'relu')(x)
x = tf.keras.layers.MaxPooling2D((2, 2))(x)
x = tf.keras.layers.Dropout(.2, input_shape=(2,))(x)

x = tf.keras.layers.Conv2D(64, (3, 3), padding = 'same', activation = 'relu')(x)
x = tf.keras.layers.Conv2D(64, (3, 3), padding = 'same', activation = 'relu')(x)
x = tf.keras.layers.MaxPooling2D((2, 2))(x)

x = tf.keras.layers.Flatten()(x)
x = tf.keras.layers.BatchNormalization()(x)

x = tf.keras.layers.Dense(5,  
                          activation='softmax', 
                          kernel_regularizer=tf.keras.regularizers.l1(1e-4))(x)

VGG_model_multiclass =  tf.keras.Model(inputs = base_model_VGG.input, outputs=x)

VGG_model_multiclass.compile(optimizer='adam', loss=['mse', 'categorical_crossentropy'], metrics=['accuracy'])

es_callback = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=3)

class_weights = {0: 2.5, 1: 3., 2: 0.2, 3: 0.3, 4: 0.8}

history_VGG_model_multiclass = VGG_model_multiclass.fit(train_ds, epochs=10, steps_per_epoch=10, callbacks=[es_callback], class_weight = class_weights , validation_data=validation_ds, validation_steps=2)

VGG_model_multiclass.summary()

plot_model_history(history_VGG_model_multiclass)

test_pred_VGG_model_multiclass = VGG_model_multiclass.predict(predict_generator(imagePaths_test), steps=len(imagePaths_test))
test_pred_VGG_model_multiclass

show_images_predict_class(imagePaths_test,test_pred_VGG_model_multiclass, 4,  10)

VGG_model_multiclass.save(path.join(project_path,'models/VGG_multiclass_model.h5'))



"""## 4.3 Оценка моделей"""

classifiers = {
  #'clear_model' : history_model,
  'VGG': history_VGG,
  'VGG_model_status': history_VGG_model_status,
  'VGG_model_multiclass': history_VGG_model_multiclass,
  'ResNet_model': history_ResNet_model,
  'ResNet_model_status': history_ResNet_model_status,
  'ResNet_model_multiclass': history_ResNet_model_multiclass
}

# Getting the accuracy and loss
result_ml = pd.DataFrame()
fig = plt.figure(figsize=(20, 10))
for model_history in classifiers.items():
      acc = model_history[1].history['accuracy']
      val_acc = model_history[1].history['val_accuracy']
      loss = model_history[1].history['loss']
      val_loss = model_history[1].history['val_loss']
      
      result_ml = result_ml.append({'model' : 'NN',
                              'classifier' : model_history[0],
                              'val accuracy' : val_acc,
                              'train accuracy' : acc,
                              'train loss' : loss,
                              'val loss' : val_loss,
                              } ,  ignore_index=True)

      epochs = range(len(acc))

      subplot = fig.add_subplot(2, 2, 1)
      subplot.set_title('accuracy')
      plt.plot(epochs, acc, '-o', label=model_history[0])
      plt.title('Training accuracy')
      plt.legend()
      plt.grid(linestyle='--')

      subplot = fig.add_subplot(2, 2, 3)
      subplot.set_title('accuracy')
      plt.plot(epochs, val_acc, '-', label=model_history[0])
      plt.title('Validation accuracy')
      plt.legend()
      plt.grid(linestyle='--')

      subplot = fig.add_subplot(2, 2, 2)
      subplot.set_title('loss')
      plt.plot(epochs, loss, '-o', label=model_history[0] )
      plt.title('Training loss')
      plt.legend()
      plt.grid(linestyle='--')

      subplot = fig.add_subplot(2, 2, 4)
      subplot.set_title('loss')
      plt.plot(epochs, val_loss, '-', label=model_history[0])
      plt.title('Validation loss')
      plt.legend()
      plt.grid(linestyle='--')

plt.show()

result_ml

test_pred_df = pd.DataFrame()
for i, p in enumerate(imagePaths_test, 0):
        test_pred_df = test_pred_df.append(
                              {'filename' : p.split(os.path.sep)[-1],
                              'image' : np.array(load_image(p)),
                              'pred_ResNet_model_status' : test_pred_ResNet_model_status.flatten()[i],
                              'pred_vgg_model_status' : test_pred_VGG_model_status.flatten()[i],
                              'pred_VGG_model_multiclass' : test_pred_VGG_model_multiclass[i],
                              'pred_ResNet_model_multiclass' :  test_pred_ResNet_model_multiclass[i]
                               } ,  ignore_index=True)

test_pred_df.head(1)

y_test_pred_df = test_pred_df
y_test_pred_df = y_test_pred_df.drop(columns=['image'])

y_test_pred_df.to_csv('predict.csv')

status = [0,0,0,0,0,0,0,0,0,0,1,1,1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,1,1,1,1,1]

y_true = status 
y_pred = test_pred_df['pred_ResNet_model_status']


print('F1 : %s' % f1_score(y_true, y_pred.round(), average='weighted'))
print('Precision : %s' % precision_score(y_true, y_pred.round(), average='weighted')) 
print('Accuracy: %s' % accuracy_score(y_true, y_pred.round()))
print('Recall: %s' % recall_score(y_true, y_pred.round()))
confusion_matrix(y_true,  y_pred.round())

y_true = pd.Series(y_true, name='Actual')
y_pred = pd.Series(y_pred, name='Predicted')
df_confusion = pd.crosstab(y_true, y_pred.round())
plot_confusion_matrix(df_confusion)

y_true = status 
y_pred = test_pred_df['pred_vgg_model_status']


print('F1 : %s' % f1_score(y_true, y_pred.round(), average='weighted'))
print('Precision : %s' % precision_score(y_true, y_pred.round(), average='weighted')) 
print('Accuracy: %s' % accuracy_score(y_true, y_pred.round()))
print('Recall: %s' % recall_score(y_true, y_pred.round()))
confusion_matrix(y_true,  y_pred.round())

y_true = pd.Series(y_true, name='Actual')
y_pred = pd.Series(y_pred, name='Predicted')
df_confusion = pd.crosstab(y_true, y_pred.round())
plot_confusion_matrix(df_confusion)

multiclass = [[1,	0,	1,	0,	0],[1,	1,	1,	0,	0],[0,	1,	1,	0,	0],[1,	1,	1,	0,	0],[1,	1,	1,	0,	0],[1,	0,	1,	0,	0],[1,	1,	1,	0,	0],[1,	0,	1,	0,	0],[1,	0,	1,	0,	0],[1,	1,	1,	0,	0],[0,	0,	0,	0,	1],[0,	0,	0,	0,	1],[0,	0,	1,	0,	0],[1,	0,	1,	0,	0],[0,	0,	0,	0,	1],[0,	0,	0,	0,	1],[0,	0,	0,	0,	1],[0,	0,	0,	0,	1],[0,	0,	0,	0,	1],[0,	0,	1,	0,	0],[0,	0,	1,	0,	0],[0,	0,	1,	0,	0],[0,	0,	1,	0,	0],[0,	0,	1,	0,	0],[0,	0,	1,	0,	0],[0,	0,	0,	0,	1],[0,	0,	0,	1,	0],[0,	0,	0,	1,	0],[0,	0,	0,	0,	1],[0,	0,	0,	0,	1],[1,	0,	1,	0,	0],[1,	1,	1,	0,	0],[1,	0,	1,	0,	0],[1,	0,	1,	0,	0],[1,	1,	1,	0,	0],[1,	1,	1,	0,	0],[0,	1,	1,	0,	0],[1,	0,	0,	1,	0],[1,	0,	1,	0,	0],[1,	1,	1,	0,	0],[0,	0,	0,	1,	0],[0,	0,	1,	0,	0],[0,	0,	1,	0,	0],[0,	0,	0,	1,	0],[0,	0,	0,	0,	1]]

multiclass_df = pd.DataFrame(multiclass)

pred_df = pd.DataFrame(test_pred_df['pred_ResNet_model_multiclass'].to_list()).round()
pred_df

y_true = multiclass_df[0]
y_pred = pred_df[0]

y_true = multiclass_df[0]
y_pred = pred_df[0]
print('F1 : %s' % f1_score(y_true, y_pred.round(), average='weighted'))
print('Precision : %s' % precision_score(y_true, y_pred.round(), average='weighted')) 
print('Accuracy: %s' % accuracy_score(y_true, y_pred.round()))
print('Recall: %s' % recall_score(y_true, y_pred.round()))
y_true = multiclass_df[1]
y_pred = pred_df[1]
print('F1 : %s' % f1_score(y_true, y_pred.round(), average='weighted'))
print('Precision : %s' % precision_score(y_true, y_pred.round(), average='weighted')) 
print('Accuracy: %s' % accuracy_score(y_true, y_pred.round()))
print('Recall: %s' % recall_score(y_true, y_pred.round()))
y_true = multiclass_df[2]
y_pred = pred_df[2]
print('F1 : %s' % f1_score(y_true, y_pred.round(), average='weighted'))
print('Precision : %s' % precision_score(y_true, y_pred.round(), average='weighted')) 
print('Accuracy: %s' % accuracy_score(y_true, y_pred.round()))
print('Recall: %s' % recall_score(y_true, y_pred.round()))
y_true = multiclass_df[3]
y_pred = pred_df[3]
print('F1 : %s' % f1_score(y_true, y_pred.round(), average='weighted'))
print('Precision : %s' % precision_score(y_true, y_pred.round(), average='weighted')) 
print('Accuracy: %s' % accuracy_score(y_true, y_pred.round()))
print('Recall: %s' % recall_score(y_true, y_pred.round()))
y_true = multiclass_df[4]
y_pred = pred_df[4]
print('F1 : %s' % f1_score(y_true, y_pred.round(), average='weighted'))
print('Precision : %s' % precision_score(y_true, y_pred.round(), average='weighted')) 
print('Accuracy: %s' % accuracy_score(y_true, y_pred.round()))
print('Recall: %s' % recall_score(y_true, y_pred.round()))

"""# Deployment

Обработка входного изображения и выдача результата:
"""

ResNet_model_status= tf.keras.models.load_model(path.join(project_path,'models/resnet_model_status.h5'))
VGG_model_status= tf.keras.models.load_model(path.join(project_path,'models/VGG_model_status.h5'))

ResNet_model_multiclass = tf.keras.models.load_model(path.join(project_path,'models/resnet_multiclass_model.h5'))
VGG_model_multiclass = tf.keras.models.load_model(path.join(project_path,'models/VGG_multiclass_model.h5'))

imagePaths = [path.join(project_path,'data/raw/img/img.jpg')]
images_ds = predict_generator(imagePaths)

y_pred_resnet_status = ResNet_model_status.predict(images_ds, steps=len(imagePaths))
y_pred_vgg_status = VGG_model_status.predict(images_ds, steps=len(imagePaths))

y_pred_resnet = ResNet_model_multiclass.predict(images_ds, steps=len(imagePaths))
y_pred_vgg = VGG_model_multiclass.predict(images_ds, steps=len(imagePaths))


for i in range(len(imagePaths)): 
  plt.imshow(load_image(imagePaths[i]), cmap='gray');
  plt.show()
  prob_resnet_status = y_pred_resnet_status[i] 
  prob_vgg_status = y_pred_vgg_status[i] 
  prob_resnet = y_pred_resnet[i] 
  prob_vgg = y_pred_vgg[i] 
  print('Predictions probabilities Resnet - VGG: \nstatus class')
  print('0-alert/1-normal - ',np.round(prob_resnet_status[0],3),'- ',np.round(prob_vgg_status[0],3))
  print('\nactivity class')
  print('pillar - ',np.round(prob_resnet[0],3),'- ',np.round(prob_vgg[0],3))
  print('lava   - ',np.round(prob_resnet[1],3),'- ',np.round(prob_vgg[1],3))
  print('\nvisible class')
  print('clear - ',np.round(prob_resnet[2],3),'- ',np.round(prob_vgg[2],3))
  print('cloud - ',np.round(prob_resnet[3],3),'- ',np.round(prob_vgg[3],3))
  print('mist  - ',np.round(prob_resnet[4],3),'- ',np.round(prob_vgg[4],3))

imagePaths = [path.join(project_path,'data/raw/img/img.jpg'),path.join(project_path,'data/raw/img/img2.jpg')]
images_ds = predict_generator(imagePaths)

y_pred_resnet_status = ResNet_model_status.predict(images_ds, steps=len(imagePaths))
y_pred_vgg_status = VGG_model_status.predict(images_ds, steps=len(imagePaths))

y_pred_resnet = ResNet_model_multiclass.predict(images_ds, steps=len(imagePaths))
y_pred_vgg = VGG_model_multiclass.predict(images_ds, steps=len(imagePaths))

for i in range(len(imagePaths)): 
  plt.imshow(load_image(imagePaths[i]), cmap='gray');
  plt.show()
  prob_resnet_status = y_pred_resnet_status[i] 
  prob_vgg_status = y_pred_vgg_status[i] 
  prob_resnet = y_pred_resnet[i] 
  prob_vgg = y_pred_vgg[i] 
  print('Predictions probabilities Resnet - VGG: \nstatus class')
  print('0-alert/1-normal - ',np.round(prob_resnet_status[0],3),'- ',np.round(prob_vgg_status[0],3))
  print('\nactivity class')
  print('pillar - ',np.round(prob_resnet[0],3),'- ',np.round(prob_vgg[0],3))
  print('lava   - ',np.round(prob_resnet[1],3),'- ',np.round(prob_vgg[1],3))
  print('\nvisible class')
  print('clear - ',np.round(prob_resnet[2],3),'- ',np.round(prob_vgg[2],3))
  print('cloud - ',np.round(prob_resnet[3],3),'- ',np.round(prob_vgg[3],3))
  print('mist  - ',np.round(prob_resnet[4],3),'- ',np.round(prob_vgg[4],3))

show_images_predict_class(imagePaths,y_pred_resnet, 6,  6)

y_pred_resnet_df = pd.DataFrame(y_pred_resnet)
y_pred_resnet_df