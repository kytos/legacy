import logging
from logging import getLogger
from threading import Lock

#: Seconds to wait before asking for more statistics.
#: Delete RRDs everytime this interval is changed
STATS_INTERVAL = 5
# STATS_INTERVAL = 1  # 1 second for testing - check RRD._get_archives()
log = getLogger(__name__)
#: Avoid segmentation fault
rrd_lock = Lock()
