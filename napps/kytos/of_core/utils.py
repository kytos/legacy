import struct

from kytos.core import log

from pyof.foundation.exceptions import UnpackException
from pyof.v0x01.common.header import Header
from pyof.v0x01.common.utils import new_message_from_header


def of_slicer(remaining_data):
    """Slice a raw bytes into OpenFlow packets"""
    data_len = len(remaining_data)
    pkts = []
    while data_len > 3:
        length_field = struct.unpack('!H', remaining_data[2:4])[0]
        if data_len >= length_field:
            pkts.append(remaining_data[:length_field])
            remaining_data = remaining_data[length_field:]
            data_len = len(remaining_data)
        else:
            break
    return pkts, remaining_data


def unpack(packet):
    """Unpacks the OpenFlow packet and returns a message."""
    try:
        header = Header()
        header.unpack(packet[:8])
        message = new_message_from_header(header)
        binary_data = packet[8:]
        if binary_data:
            message.unpack(binary_data)
        return message
    except (UnpackException, ValueError) as e:
        log.info('Could not unpack message: %s', packet)
        raise UnpackException(e)
