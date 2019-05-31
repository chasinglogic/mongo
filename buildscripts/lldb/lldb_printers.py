"""LLDB Pretty-printers for MongoDB.

To import script in lldb, run:

   command script import buildscripts/lldb/lldb_printers.py

This file must maintain Python 2 and 3 compatibility until Apple
upgrades to Python 3 and updates their LLDB to point to it.
"""
from __future__ import print_function

import lldb
import string
import struct
import sys

try:
    import bson
    import bson.json_util
    from bson import json_util

    import collections
    # TODO verify this and see if it can be resolved.
    # Apple LLDB which is linked against Apple Python hits an error on the following import
    # Traceback (most recent call last):
    # File "<input>", line 1, in <module>
    # File "/Library/Python/2.7/site-packages/bson/codec_options.py", line 21, in <module>
    #     from bson.py3compat import abc, string_type
    # ImportError: cannot import name abc
    from bson.codec_options import CodecOptions
except ImportError as err:
    print("Warning: Could not load bson library for Python {}.".format(sys.version))
    print("Check with the pip command if pymongo 3.x is installed.")
    bson = None


def __lldb_init_module(debugger, dict):
    debugger.HandleCommand("type summary add -F lldb_printers.StringDataSummary mongo::StringData")
    debugger.HandleCommand("type summary add -F lldb_printers.BSONObjSummary mongo::BSONObj")
    debugger.HandleCommand("type summary add -s 'A${*var.__ptr_.__value_}' -x '^std::__1::unique_ptr<.+>$'")
    debugger.HandleCommand("type synthetic add --python-class lldb_printers.UniquePtrSynth -x '^std::__1::unique_ptr<.+>$'")
    debugger.HandleCommand("type synthetic add --python-class lldb_printers.OptionalSynth -x '^boost::optional<.+>$'")
    # debugger.HandleCommand("type synthetic add mongo::BSONObj --python-class lldb_printers.BSONObjSynth")
    # debugger.HandleCommand("type summary add -F lldb_printers.StringDataSummary mongo::Status")
    # debugger.HandleCommand("type summary add -F lldb_printers.StringDataSummary mongo::StatusWith")


def StringDataSummary(valobj, *args):
    ptr = valobj.GetChildMemberWithName("_data").GetValueAsUnsigned()
    size1 = valobj.GetChildMemberWithName("_size").GetValueAsUnsigned(0)
    return '"{}"'.format(valobj.GetProcess().ReadMemory(ptr, size1, lldb.SBError()).encode("utf-8"))


def BSONObjSummary(valobj, *args):
    ptr = valobj.GetChildMemberWithName("_objdata").GetValueAsUnsigned()
    size = struct.unpack("<I", valobj.GetProcess().ReadMemory(ptr, 4, lldb.SBError()))[0]
    if size < 5 or size > 17 * 1024 * 1024:
        return
    buf = bson.BSON(bytes(valobj.GetProcess().ReadMemory(ptr, size, lldb.SBError())))
    return json_util.dumps(buf.decode())


# def UniquePtrSummary(valobj, dict);
#         ptr = valobj.GetChildMemberWithName("_objdata").GetValueAsUnsigned()

class UniquePtrSynth:
    def __init__(self, valobj, dict):
        print("init caled");
        self.valobj = valobj
        self.update()

    def num_children(self):
        print("num child caled");
        return 1

    def get_child_index(self, name):
        print("get child caled: " + name);
        if name == "ptr":
            return 0
        else:
            return None

    def get_child_at_index(self, index):
        print("get child at index caled: " + str(index) );
        if index == 0:
            return self.valobj.GetChildMemberWithName("__ptr_").GetChildMemberWithName("__value_").Dereference()
        else:
            return None

    def has_children():
        print("has child calld");
        return True

    def update(self):
        pass


class OptionalSynth:
    def __init__(self, valobj, dict):
        print("init caled");
        self.valobj = valobj
        self.update()

    def num_children(self):
        print("num child caled");
        return 1

    def get_child_index(self, name):
        print("get child caled: " + name);
        if name == "value":
            return 0
        else:
            return None

    def get_child_at_index(self, index):
        print("get child at index caled: " + str(index) );
        if index == 0:
            return self.value
        else:
            return None

    def has_children():
        print("has child calld");
        return True

    def update(self):
        self.is_init = self.valobj.GetChildMemberWithName("m_initialized").GetValueAsUnsigned() != 0
        self.value = None
        if self.is_init:
            temp_type = self.valobj.GetType().GetTemplateArgumentType(0)
            storage = self.GetChildMemberWithName("m_storage")
            self.value = storage.Cast(temp_type)

print( "done")

#    return "unknown"

# class BSONObjSynth:
#     def __init__(self, valobj, dict):
#         self.valobj = valobj;
#         self.update()

#     def num_children(self):

#     def get_child_index(self, name):

#     def get_child_at_index(self, index):
#         return self.begin.CreateChildAtOffset("["+str(index)+"]",
#                                               offset, self.data_type)

#     def update(self):
#         self.begin = self.valobj.GetChildMemberWithName("BeginX")
#         self.size = self.valobj.GetChildMemberWithName("Size")
#         the_type = self.valobj.GetType()
#         # If this is a reference type we have to dereference it to get to the
#         # template parameter.
#         if the_type.IsReferenceType():
#             the_type = the_type.GetDereferencedType()

#         self.data_type = the_type.GetTemplateArgumentType(0)
#         self.type_size = self.data_type.GetByteSize()
#         assert self.type_size != 0

