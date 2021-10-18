import tensorflow.compat.v1 as tf
from .se_resnet import SEResnet, PixelShuffleTorch


def DUC(x, filters, upscale_factor=2, name=None):
    x = tf.keras.layers.ZeroPadding2D(padding=(1, 1))(x)
    x = tf.keras.layers.Conv2D(filters=filters,
                               kernel_size=(3, 3),
                               padding='valid',
                               use_bias=False,
                               name=name + "." + "conv")(x)

    x = tf.keras.layers.BatchNormalization(momentum=0.1, epsilon=1e-05, name=name + "." + "bn")(x)
    x = tf.keras.layers.ReLU(name=name + "." + "relu")(x)
    x = PixelShuffleTorch(upscale_factor, name=name + "." + "pixel_shuffle")(x)

    return x


def FastPose(x):
    out = SEResnet(x, name="preact")
    out = PixelShuffleTorch(2, name="pixel_shuffle")(out)

    out = DUC(out, 1024, upscale_factor=2, name="duc1")
    out = DUC(out, 512, upscale_factor=2, name="duc2")
    out = tf.keras.layers.ZeroPadding2D(padding=(1, 1))(out)
    out = tf.keras.layers.Conv2D(filters=17,
                                 kernel_size=(3, 3),
                                 padding='valid',
                                 name='conv_out')(out)
    return out
