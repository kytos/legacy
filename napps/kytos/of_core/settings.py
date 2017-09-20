"""Settings for the of_core NApp.."""
#: Pooling frequency
STATS_INTERVAL = 5

#: Supported Versions
OPENFLOW_VERSIONS = [0x01, 0x04]

#: If SEND_FEATURES_REQUEST_ON_ECHO is True, kytos/of_core must send
#: FeaturesRequest when when it sends an echo reply message
SEND_FEATURES_REQUEST_ON_ECHO = False

#: Send Echo requests to switches periodically to keep connection
SEND_ECHO_REQUESTS = True

#: Send Set Config messages right after the OpenFlow handshake
SEND_SET_CONFIG = True
