import os
from os.path import basename, join, exists
import numpy as np
np.random.seed(777)
import time
import tensorflow as tf
import keras as keras
from keras.preprocessing import image
from keras.preprocessing.image import ImageDataGenerator
from keras.applications.vgg16 import decode_predictions
from keras.models import Sequential
from keras.layers import Dense,Activation,Flatten
from keras.layers import merge,Input
from keras.models import Model
from keras.utils import np_utils
from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split
import os
from keras.preprocessing.image import ImageDataGenerator
# DCNN Models used
#---------------------------------------------
from keras.applications.vgg16 import VGG16
#----------------------------------------------
from keras.applications.vgg16 import preprocess_input as pi_vgg16
from keras.models import load_model
from numpy import array
from numpy import argmax
from sklearn.metrics import accuracy_score
from  numpy import mean 
from numpy import std
import matplotlib.pyplot as plt
from keras.optimizers import Adam,SGD
from keras.callbacks import ReduceLROnPlateau,EarlyStopping,ModelCheckpoint
from keras.layers import GlobalAveragePooling2D, Concatenate
from keras.layers import BatchNormalization,Dropout
from keras.layers import Lambda
from keras.regularizers import l2
import math
from keras import utils as np_utils
from keras import backend as K
from keras.metrics import categorical_accuracy
import warnings
warnings.filterwarnings('always')
warnings.filterwarnings('ignore')
from keras.models import load_model
os.chdir(r"COVID_Xray/")

train_dir="aug/"
test_dir="test/"

total=0
print('---Training set details----')
for sub_folder in os.listdir(train_dir):
  no_of_images=len(os.listdir(train_dir + sub_folder))
  total+=no_of_images
  print(str(no_of_images) + " " + sub_folder + " images")

print("Total no. of Chest Xray training images=",total)

total=0
print('---Test set details----')
for sub_folder in os.listdir(test_dir):
  no_of_images=len(os.listdir(test_dir + sub_folder))
  total+=no_of_images
  print(str(no_of_images) + " " + sub_folder + " images")

print("Total no. of Chest Xray test images=",total)

extracted_features_dir="COVID_Xray/extracted_features/"

img_height =512
img_width =512
batch_size =32
input_shape = (img_width, img_height, 3)

print("-----------------Image Augmentation for VGG16--------------")

random_seed = np.random.seed(1142)
train_datagen = ImageDataGenerator(
    rescale=1./255,
    featurewise_center=True,
    featurewise_std_normalization=True,
    rotation_range=15,
    width_shift_range=0.2,
    height_shift_range=0.2,
    validation_split= 0.2,
    zoom_range=0.1,
    shear_range=0.2)

train_generator_vgg16 = train_datagen.flow_from_directory(
    train_dir,
    target_size=(img_height, img_width),
    batch_size=batch_size,
    seed = random_seed,
    shuffle=False,
    subset = 'training',
    class_mode='categorical')

val_generator_vgg16 = train_datagen.flow_from_directory(
    train_dir,
    target_size=(img_height, img_width),
    batch_size=batch_size,
    seed = random_seed,
    shuffle=False,
    subset = 'validation',
    class_mode='categorical')

test_datagen=ImageDataGenerator(rescale=1./255)
test_generator_vgg16=test_datagen.flow_from_directory(test_dir,
                                                      target_size=(img_height, img_width),
                                                          batch_size=batch_size, 
                                                          seed=random_seed,
                                                          shuffle=False,
                                                          class_mode='categorical') 

nb_train_samples = len(train_generator_vgg16.filenames)
nb_validation_samples = len(val_generator_vgg16.filenames)
predict_size_train = int(math.ceil(nb_train_samples / batch_size))
predict_size_validation = int(math.ceil(nb_validation_samples / batch_size))

nb_test_samples = len(test_generator_vgg16.filenames)
predict_size_test = int(math.ceil(nb_test_samples / batch_size))

model_name="VGG16"
model = VGG16(include_top=False, weights="imagenet",pooling='avg',input_shape=input_shape)
image_input =model.input

x1= layers.GlobalAveragePooling2D()(model.get_layer("block2_conv2").output)
x2= layers.GlobalAveragePooling2D()(model.get_layer("block3_conv3").output)
x3 = layers.GlobalAveragePooling2D()(model.get_layer("block4_conv3").output)  
x4 = layers.GlobalAveragePooling2D()(model.get_layer("block5_conv3").output)  
out= layers.Concatenate()([x1,x2,x3,x4])
out=layers.Dense(512,activation='relu')(out)
out=layers.Dropout(0.5)(out)
out=layers.Dense(3,activation='softmax',name= 'output')(out)
custom_vgg16_model = models.Model(image_input , out)
custom_vgg16_model.summary()

for layer in custom_vgg16_model.layers[:15]:
    layer.trainable = False
custom_vgg16_model.summary()

nEpochs=100
base_lr=1e-3
lr_min=0
alpha=1
def lr_scheduler(epoch):
    lr = math.fabs(lr_min + (1 + math.cos(1 * epoch * math.pi /nEpochs)) * (base_lr - lr_min) / 2.)
    print('lr: %f' % lr)
    return lr

contr_loss=tfa.losses.contrastive_loss

opt = optimizers.Adam(lr=base_lr, beta_1=0.6, beta_2=0.8,amsgrad=True)
custom_vgg16_model.compile(optimizer = opt, loss=['categorical_crossentropy',contr_loss], metrics=['accuracy'])
checkpoint1 = callbacks.ModelCheckpoint('/content/drive/MyDrive/COVID/saved models/VGG16/vgg16model_weights.h5', monitor='val_accuracy', verbose=1, save_best_only=True, mode='max')
lr_decay = callbacks.LearningRateScheduler(schedule=lr_scheduler)
callbacks_list=[checkpoint1,lr_decay]
#training the modified VGG16 network for refining the deep feature embedding
history =custom_vgg16_model.fit(train_generator_vgg16,
                    epochs=nEpochs,
                    validation_data=val_generator_vgg16,
                    callbacks=callbacks_list)

#Saving features of the training images
features_train = custom_vgg16_model.predict_generator(train_generator_vgg16, predict_size_train)
np.save(extracted_features_dir+model_name+'_train_features.npy', features_train)

# Saving features of the validation images
features_validation = custom_vgg16_model.predict_generator(val_generator_vgg16, predict_size_validation)
np.save(extracted_features_dir+model_name+'_val_features.npy', features_validation)

# Saving features of the test images
features_test = custom_vgg16_model.predict_generator(test_generator_vgg16, predict_size_test)
np.save(extracted_features_dir+model_name+'_test_features.npy', features_test)

