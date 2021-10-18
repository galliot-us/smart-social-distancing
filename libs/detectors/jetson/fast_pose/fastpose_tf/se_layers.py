import tensorflow.compat.v1 as tf


def SELayer(x, channel, reduction=1, name=None):
    b, c = x.shape[0], x.shape[3]  # TODO: change it for using first channel
    y = tf.keras.layers.GlobalAveragePooling2D(name=name + "." + "avg_pool")(x)
    #    y = tf.reshape(y, shape=tf.convert_to_tensor([b, c]))  # .view at pytroch
    y = tf.keras.layers.Reshape((c,))(y)
    y = tf.keras.layers.Dense(units=channel // reduction, name=name + "." + "fc" + "." + "0")(y)
    y = tf.keras.layers.ReLU(name=name + "." + "fc" + "." + "1")(y)
    y = tf.keras.layers.Dense(units=channel, name=name + "." + "fc" + "." + "2")(y)
    y = tf.keras.activations.sigmoid(y)
    #    y = tf.reshape(y, shape=[b, 1, 1, c])
    y = tf.keras.layers.Reshape((1, 1, c))(y)
    return x * y
