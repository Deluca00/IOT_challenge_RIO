import os
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Activation, Flatten, Dropout
from tensorflow.keras.layers import Conv2D, MaxPooling2D

from mltk.core.model import (
    MltkModel,
    TrainMixin,
    ImageDatasetMixin,
    EvaluateClassifierMixin
)
from mltk.core.preprocess.image.parallel_generator import ParallelImageDataGenerator
from mltk.datasets.image import rock_paper_scissors_v2

# ======================================================
# B2: Khai báo model MLTK
# ======================================================
class MyModel(
    MltkModel,
    TrainMixin,
    ImageDatasetMixin,
    EvaluateClassifierMixin
):
    pass

my_model = MyModel()
my_model.version = 1
my_model.description = 'Rock/Paper/Scissors classifier'

# Training config
my_model.epochs = 30
my_model.batch_size = 32
my_model.optimizer = 'adam'
my_model.metrics = ['accuracy']
my_model.loss = 'categorical_crossentropy'

my_model.checkpoint['monitor'] = 'val_accuracy'
my_model.reduce_lr_on_plateau = dict(
    monitor='loss',
    factor=0.95,
    min_delta=0.001,
    patience=1
)
my_model.early_stopping = dict(
    monitor='accuracy',
    patience=10,
    verbose=1
)

# TFLite quantization
my_model.tflite_converter['optimizations'] = ['DEFAULT']
my_model.tflite_converter['inference_input_type'] = 'float32'
my_model.tflite_converter['inference_output_type'] = 'float32'
my_model.tflite_converter['representative_dataset'] = 'generate'

# Dataset config
my_model.dataset = 'rock_paper_scissors_v2'
my_model.class_mode = 'categorical'
my_model.classes = ['rock', 'paper', 'scissor', '_unknown_']
my_model.input_shape = (84, 84, 1)
my_model.shuffle_dataset_enabled = True
my_model.class_weights = 'balanced'

# Data augmentation
my_model.datagen = ParallelImageDataGenerator(
    cores=0.65,
    debug=False,
    max_batches_pending=32,
    validation_split=0.1,  # để MLTK tự chia val từ train
    validation_augmentation_enabled=False,
    rotation_range=15,
    width_shift_range=5,
    height_shift_range=5,
    brightness_range=(0.80, 1.10),
    contrast_range=(0.80, 1.10),
    noise=['gauss', 'poisson', 's&p'],
    zoom_range=(0.95, 1.05),
    rescale=None,
    horizontal_flip=True,
    vertical_flip=True,
    samplewise_center=True,
    samplewise_std_normalization=True,
)

# ======================================================
# B3: Định nghĩa kiến trúc CNN
# ======================================================
def my_model_builder(model: MyModel):
    keras_model = Sequential()
    filter_count = 16

    keras_model.add(Conv2D(filter_count, (3, 3), input_shape=model.input_shape))
    keras_model.add(Activation('relu'))
    keras_model.add(MaxPooling2D(pool_size=(2, 2)))

    keras_model.add(Conv2D(filter_count, (3, 3)))
    keras_model.add(Activation('relu'))
    keras_model.add(MaxPooling2D(pool_size=(2, 2)))

    keras_model.add(Conv2D(filter_count*2, (3, 3)))
    keras_model.add(Activation('relu'))
    keras_model.add(MaxPooling2D(pool_size=(2, 2)))

    keras_model.add(Flatten())
    keras_model.add(Dense(filter_count*2))
    keras_model.add(Activation('relu'))
    keras_model.add(Dropout(0.5))
    keras_model.add(Dense(model.n_classes, activation='softmax'))

    keras_model.compile(
        loss=model.loss,
        optimizer=model.optimizer,
        metrics=model.metrics
    )
    return keras_model

my_model.build_model_function = my_model_builder

print("✅ Model config đã sẵn sàng để train/test")
