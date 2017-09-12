import struct

import pyof.v0x01 as pyof_01
import pyof.v0x04 as pyof_04

from collections import OrderedDict

from kytos.core import KytosEvent, log

from pyof.foundation.exceptions import PackException, UnpackException
from pyof.v0x01.common.header import Type as OFPTYPE

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


def _unpack_int(packet, offset=0, size=None):
    if size is None:
        if type(packet) == int:
            return packet
        size = len(packet)
    return int.from_bytes(packet[offset:offset + size], byteorder='big')


def _emit_message(controller, connection, message, direction):
    """Make controller emit a KytosEvent for an incoming/outgoing message
    containing the message and the source."""
    if direction == 'in':
        address_type = 'source'
        message_buffer = controller.buffers.msg_in
    elif direction == 'out':
        address_type = 'destination'
        message_buffer = controller.buffers.msg_out
    else:
        raise Exception("direction must be 'in' or 'out'")

    name = message.header.message_type.name.lower()
    hex_version = 'v0x%0.2x' % (message.header.version + 0)
    of_event = KytosEvent(
        name=f"kytos/of_core.{hex_version}.messages.{direction}.{name}",
        content={'message': message,
                 address_type: connection})
    message_buffer.put(of_event)


def emit_message_in(controller, connection, message):
    """Make controller emit a KytosEvent for an incoming message
    containing the message and the source."""
    _emit_message(controller, connection, message, 'in')


def emit_message_out(controller, connection, message):
    """Make controller emit a KytosEvent for an outgoing message
    containing the message and the destination."""
    _emit_message(controller, connection, message, 'out')


class GenericHello():
    """Version agnostic OpenFlow Hello Message"""
    header_sizes = OrderedDict(
        version=1,
        type=1,
        length=2,
        xid=4)

    elem_type_size = 2
    elem_len_size = 2

    OFPHET_VERSIONBITMAP = 1

    class generic_Header():
        pass

    def __init__(self, *, packet=None, versions=None, xid=None):
        """Initialize a GenericHello instance from a binary packet or from
            initial versions and xid parameters.

            Parameters:
                packet: binary packet (bytes) to be unpacked and used to
                        initialize the message
                versions: list of versions used to build the version bitmap
                xid: xid to be used in the message
        """
        self.header = self.generic_Header()
        self.header.message_type = OFPTYPE.OFPT_HELLO
        if not any((packet, versions)):
            raise Exception('either packet or versions must be set.')

        if packet is not None:
            self.unpack(packet)
        else:
            if xid is None:
                self.header.xid = 0

        if versions is not None:
            self.versions = versions
            self.header.version = max(versions)
        if xid is not None:
            self.header.xid = xid

    def pack(self):
        versions = self.versions
        xid = self.header.xid
        packet_version = max(versions)
        if packet_version > 31:
            raise PackException
        versions_value = 0
        for version in versions:
            versions_value += (1 << version)
        bitmap = versions_value.to_bytes(4, byteorder='big')
        version_byte = packet_version.to_bytes(self.header_sizes['version'],
                                               byteorder='big')
        xid_byte = xid.to_bytes(self.header_sizes['xid'],
                                byteorder='big')
        packet = version_byte + b'\x00\x00\x10' + xid_byte + \
            b'\x00\x01\x00\x08' + bitmap
        return packet

    def unpack(self, packet):
        offset = 0
        # self.header = self.generic_Header()
        for key, size in self.header_sizes.items():
            setattr(self.header, key, _unpack_int(packet, offset, size))
            offset += size

        if (self.header.type != 0):
            raise UnpackException

        elements = {}
        try:
            while offset < self.header.length:
                elem_type = _unpack_int(
                    packet, offset, self.elem_type_size)

                offset += self.elem_type_size
                elem_length = _unpack_int(
                    packet, offset, self.elem_len_size)

                offset += self.elem_len_size
                elem_header_size = self.elem_type_size - self.elem_len_size
                elem_value_size = elem_length - elem_header_size
                elem_value = _unpack_int(
                    packet, offset, elem_value_size)

                elements[elem_type] = elem_value
        except IndexError:
            raise UnpackException

        self.elements = elements

        if self.OFPHET_VERSIONBITMAP in self.elements:
            bitmap = self.elements[self.OFPHET_VERSIONBITMAP]
            versions = []
            for i in range(32):
                if ((1 << i) & bitmap) != 0:
                    versions.append(i)
            self.versions = versions
            self.version_bitmap = bitmap
        else:
            self.versions = None


class NegotiationException(Exception):
    """OF version negotiation failed Exception"""

    def __str__(self):
        return "OF version negotiation failed: " + super().__str__()
