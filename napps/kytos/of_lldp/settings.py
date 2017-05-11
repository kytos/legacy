"""Settings for the of_lldp NApp."""
POOLING_TIME = 3

# If we receive LLDP Packets that does not fit our format/needs, we will ignore
# it. But it can be logged for trace/debug purposes. Here we need to define the
# logLevel we want for this packets as a string (DEBUG, INFO, WARNING, etc) or
# None (python None type)
UNKOWN_LLDP_PACKETS_LOG_LEVEL = 'WARNING'
