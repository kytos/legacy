"""Settings file for the NApp kytos/of_stats."""
from pathlib import Path
from threading import Lock

#: Seconds to wait before asking for more statistics.
#: Delete RRDs everytime this interval is changed
STATS_INTERVAL = 30
# STATS_INTERVAL = 1  # 1 second for testing - check RRD._get_archives()

#: Avoid segmentation fault
rrd_lock = Lock()

# RRD Tool Settings

DIR = Path(__file__).parent / 'rrd'

# If no new data is supplied for more than *_TIMEOUT* seconds,
# the temperature becomes *UNKNOWN*.
TIMEOUT = 2 * STATS_INTERVAL

# Minimum accepted value
MIN = 0

# Maximum accepted value is the maximum PortStats attribute value.
MAX = 2 ** 64 - 1

# The xfiles factor defines what part of a consolidation interval may be
# made up from *UNKNOWN* data while the consolidated value is still
# regarded as known. It is given as the ratio of allowed *UNKNOWN* PDPs
# to the number of PDPs in the interval. Thus, it ranges from 0 to 1
# (exclusive).
XFF = '0.5'

# How long to keep the data. Accepts s (seconds), m (minutes), h (hours),
# d (days), w (weeks), M (months), and y (years).
# Must be a multiple of consolidation steps.
PERIOD = '30d'
