#+
# Common definitions for example chunk protocol.
#
# Copyright 2020 by Lawrence D'Oliveiro <ldo@geek-central.gen.nz>. This
# script is licensed CC0
# <https://creativecommons.org/publicdomain/zero/1.0/>; do with it
# what you will.
#-

import struct

#+
# Useful stuff
#-

class TIME_UNIT :
    "convenient names for various multiples of seconds of time."
    SECOND = 1
    MINUTE = 60
    HOUR = 3600
    DAY = 86400
    WEEK = 7 * DAY
#end TIME_UNIT

#+
# Protocol definitions
#-

socket_name = "/tmp/chunk_example"

class chunk :
    "Chunks are used for client-server communication. A chunk" \
    " consists of a 4-byte ID code, followed by a 4-byte integer" \
    " length (always little-endian), and then that number of bytes" \
    " of contents (which might be zero).\n" \
    "\n" \
    "More complex messages may use chunks within chunks."

    @classmethod
    def encode(chunk, contents) :
        "converts contents to a bytes object in some suitable representation."
        if isinstance(contents, str) :
            contents = contents.encode()
        elif isinstance(contents, bytes) :
            pass
        elif isinstance(contents, dict) :
            contents = b"".join \
              (
                chunk.make(key, contents[key]) for key in sorted(contents.keys())
              )
        elif isinstance(contents, (list, tuple)) :
            # assume it’s a sequence of pairs (id, contents)
            contents = b"".join \
              (
                chunk.make(*item) for item in contents
              )
        elif isinstance(contents, int) :
            contents = ("%d" % contents).encode()
        else :
            raise TypeError \
              (
                "contents must be str, bytes, dict, sequence or int, not %s" % type(contents)
              )
        #end if
        return \
            contents
    #end encode

    @classmethod
    def make(chunk, id, contents) :
        "creates a new chunk with the specified id and contents."
        contents = chunk.encode(contents)
        return \
            (
                struct.pack("<4sI", id, len(contents))
            +
                contents
            )
    #end make

    @staticmethod
    def extract_header(data) :
        "parses a chunk header into its ID and length fields."
        assert len(data) == 8
        return \
            struct.unpack("<4sI", data)
    #end extract_header

    @classmethod
    def extract(chunk, data) :
        "parses a chunk into its ID, contents and whatever comes after." \
        " Returns None if the data cannot be parsed."
        if len(data) >= 8 :
            id, length = chunk.extract_header(data[:8])
            if length + 8 <= len(data) :
                result = (id, data[8 : length + 8], data[length + 8:])
            else :
                result = None
            #end if
        else :
            result = None
        #end if
        return \
            result
    #end extract

    @classmethod
    def extract_iter(chunk, data) :
        "parses data, yielding successive pairs of chunk IDs and corresponding contents."
        while True :
            items = chunk.extract(data)
            if items == None :
                break
            yield items[0], items[1]
            data = items[2]
        #end while
    #end extract_iter

#end chunk

class ID:
    "namespace for all chunk ID codes."

    request_noop = b'NOOP'
      # no operation. No contents, response is reply_noop. May be used
      # to keep the connection from being closed due to the inactivity
      # timeout.

    reply_noop = b'NOOP'
      # reply returned when there is nothing to return. No data.

    request_shutdown = b'SHUT'
      # request to shut down the server. Response is reply_noop.

    request_echo = b'ECHO'
      # request to echo request contents back to client.
      # Response is reply_echo.

    reply_echo = b'ECHO'
      # response to request_echo. Contents equal those
      # of request.

    request_delay = b'DLAY'
      # request to delay for a specified time. Contents:
      #     interval -- interval in seconds.
      # Response (after specified delay) is reply_noop.

    request_compute = b'CMPU'
      # request to perform a computation. Contents:
      #     operator -- contains the name of the operation to perform,
      #         one of “+”, “-”, “*”, “/”, “%” or “**”.
      #     operand -- need to have two of these for “-”, “/”, “%” or “**”,
      #         while “+” and “*” can have any number of operands.
      # Response is reply_answer.

    reply_answer = b'ANSR'
      # Response to request_compute. Contents:
      #     status -- whether computation was successful or not (i.e. undefined result)
      #     value  -- the computation result, if successful.

    interval = b'NTVL'
      # decimal number string (fractional part allowed)

    operator = b'OPER'

    operand = b'OPND'
      # integer, float or complex number string

    value = b'VALU'
      # integer, float or complex number string

    status = b'STS '
      # status code, decimal integer string, value of 1 for success, 0 for failure.

#end ID
