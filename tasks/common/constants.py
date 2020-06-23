D_FRONTEND = 'frontend'
D_X86 = 'x86'
D_OPENVINO = 'openvino'
D_CORAL_DEV_BORAD = 'coral-dev-board'
D_JETSON_NANO = 'jetson-nano'
D_JETSON_TX2 = 'jetson-tx2'
D_AMD64_USBTPU = 'amd64-usbtpu'

# Keep dependencies before dependants (e.g. D_FRONTEND first)
D_ALL = [D_FRONTEND, D_X86, D_OPENVINO, D_CORAL_DEV_BORAD, D_JETSON_NANO, D_AMD64_USBTPU, D_JETSON_TX2]

D_BACKENDS = [x for x in D_ALL if x not in {D_FRONTEND}]
