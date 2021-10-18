import tensorflow.compat.v1 as tf
import itertools
import numpy as np
from .se_layers import SELayer


class PixelShuffleTorch(tf.keras.layers.Layer):
    def __init__(self, r, name=""):
        super(PixelShuffleTorch, self).__init__(name=name)
        self.r = r

    def call(self, x):
        batch_size, rows, cols, in_channels = x.get_shape().as_list()
        kernel_filter_size = self.r
        out_channels = int(in_channels // (self.r * self.r))
        kernel_shape = [kernel_filter_size, kernel_filter_size, out_channels, in_channels]
        kernel = np.zeros(kernel_shape, np.float32)
        for c in range(0, out_channels):
            i = 0
            for _x, _y in itertools.product(range(self.r), repeat=2):
                kernel[_x, _y, c, c * self.r * self.r + i] = 1
                i += 1
        new_rows, new_cols = int(rows * self.r), int(cols * self.r)
        batch_size = tf.shape(x)[0]
        tf_shape = tf.convert_to_tensor([batch_size, new_rows, new_cols, out_channels])
        strides_shape = [1, self.r, self.r, 1]
        kernel = tf.convert_to_tensor(kernel)
        out = tf.nn.conv2d_transpose(x, kernel, tf_shape, strides_shape, padding='VALID')
        return out


def Bottelneck(x, filters, stride=(1, 1), downsample=None, reduction=False, dcn=None, name=None):
    expansion = 4
    with_dcn = dcn is not None
    residual = x
    out = tf.keras.layers.ZeroPadding2D(padding=(0, 0))(x)
    out = tf.keras.layers.Conv2D(
        filters=filters,
        kernel_size=(1, 1),
        use_bias=False,
        padding='valid',
        name=name + "." + "conv1"
    )(x)
    out = tf.keras.layers.BatchNormalization(momentum=0.1, epsilon=1e-05, name=name + "." + "bn1")(out)
    out = tf.nn.relu(out)
    if not with_dcn:
        out = tf.keras.layers.ZeroPadding2D(padding=(1, 1))(out)
        out = tf.keras.layers.Conv2D(
            filters=filters,
            kernel_size=(3, 3),
            strides=stride,
            use_bias=False,
            padding='valid',
            name=name + "." + "conv2"
        )(out)
        out = tf.keras.layers.BatchNormalization(momentum=0.1, epsilon=1e-05, name=name + "." + "bn2")(out)
        out = tf.nn.relu(out)
        # else TODO
    out = tf.keras.layers.Conv2D(filters=filters * 4,
                                 kernel_size=(1, 1),
                                 use_bias=False,
                                 padding='valid',
                                 name=name + "." + "conv3")(out)
    out = tf.keras.layers.BatchNormalization(momentum=0.1, epsilon=1e-05, name=name + "." + "bn3")(out)

    if reduction:
        out = SELayer(out, filters * 4, name=name + "." + "se")

    if downsample and (stride != (1, 1) or (64 != expansion * filters)):
        residual = tf.keras.layers.Conv2D(filters=filters * expansion,
                                          kernel_size=(1, 1), strides=stride,
                                          use_bias=False, padding='valid', name=name + ".downsample.0")(x)
        residual = tf.keras.layers.BatchNormalization(momentum=0.1, epsilon=1e-05, name=name + ".downsample.1")(
            residual)

    out += residual
    out = tf.nn.relu(out)

    return out


def SEResnet(x, name=None):
    filters = 64
    block = Bottelneck
    stage_with_dcn = [False, False, False, False]
    num_layers = [3, 4, 6, 3]
    x = tf.keras.layers.ZeroPadding2D(padding=(3, 3))(x)
    x = tf.keras.layers.Conv2D(64, kernel_size=(7, 7), strides=(2, 2),
                               padding='valid', use_bias=False, name=name + "." + "conv1")(x)  # padding?
    x = tf.keras.layers.BatchNormalization(momentum=0.1, epsilon=1e-05, name=name + "." + "bn1")(x)
    x = tf.keras.layers.ReLU(name=name + "." + "relu")(x)
    x = tf.keras.layers.ZeroPadding2D(padding=(1, 1))(x)
    x = tf.keras.layers.MaxPooling2D(pool_size=(3, 3),
                                     strides=(2, 2),
                                     padding='valid',
                                     name=name + "." + "maxpool")(x)
    x = make_layer(x, block, 64, num_layers[0], dcn=None, name=name + "." + "layer1")  # 256 * h/4 * w/4
    x = make_layer(x, block, 128, num_layers[1], stride=(2, 2), dcn=None, name=name + "." + "layer2")  # 512 * h/8 * w/8
    x = make_layer(x, block, 256, num_layers[2], stride=(2, 2), dcn=None,
                   name=name + "." + "layer3")  # 1024 * h/16 * w/16
    x = make_layer(x, block, 512, num_layers[3], stride=(2, 2), dcn=None,
                   name=name + "." + "layer4")  # 2048 * h/32 * w/32
    return x


def make_layer(x, block, filters, blocks, stride=(1, 1), dcn=None, name=None):
    downsample = None
    x = block(x, filters, stride, downsample=True, reduction=True, dcn=dcn, name=name + "." + "0")
    for i in range(1, blocks):
        x = block(x, filters, dcn=dcn, name=name + "." + str(i))

    return x
