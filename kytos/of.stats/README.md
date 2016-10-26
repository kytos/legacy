Requirements
============
Besides Python packages in *requirements.txt*, [rrdtool](http://www.rrdtool.org)
is required.

API
===
```bash
FLASK_DEBUG=1 python main.py
```
*Note:* ommit `FLASK_DEBUG` when in production.

URL is of the form `/of.stats/dpid/port/start/end`, where `start` and `end` are
UNIX timestamps in seconds. More information in the source code.

Tests
=====
```bash
python -m unittest test_rrd.py
```

RRD Graphs
==========
The examples assume you are in the `rrd` folder. Example for generating a graph:

1. First, get the **first** and **last** useful timestamps with:
```bash
rrdtool fetch switch1port1.rrd AVERAGE | grep -v nan
```
1. Optionally, verify the records for the graph:
```bash
rrdtool fetch switch1port1.rrd AVERAGE --start [first-1] --end [last-1]
```
1. Then, make graph subtracting 1 from the first and last useful timestamps:
```bash
rrdtool graph speed.png --start [first-1] --end [last-1] \
  DEF:speed=switch1port1.rrd:rx_bytes:AVERAGE LINE2:speed#FF0000
```
