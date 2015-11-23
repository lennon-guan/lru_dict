#!-*- coding: utf-8 -*-

from __future__ import print_function
import sys
if '2' == sys.version[0]:
    strtype = unicode
    iter_range = xrange
elif '3' == sys.version[0]:
    strtype = str
    iter_range = range
else:
    raise RuntimeError('Unsupported python version %r.' % sys.version)
import threading

__all__ = ['LruDict', 'LruDictR']
__version__ = '0.0.1'
__author__ = 'guanming'


class _LruNode(object):
    def __init__(self):
        self._next = None
        self._prev = None
        self._key = None
        self._value = None

    def remove_from_list(self):
        next_node = self._next
        prev_node = self._prev
        if next_node:
            next_node._prev = prev_node
        if prev_node:
            prev_node._next = next_node
        return self

    def insert_before(self, target):
        self._next = target
        self._prev = target._prev
        target._prev = self
        if self._prev:
            self._prev._next = self

    def insert_after(self, target):
        self._next = target._next
        self._prev = target
        target._next = self
        if self._next:
            self._next._prev = self


class LruDict(object):
    def __init__(self, cap):
        self._kv = {}
        self._cap = cap
        self._size = 0
        self._head = _LruNode()
        self._tail = _LruNode()
        self._head._next = self._tail
        self._tail._prev = self._head

    def __setitem__(self, key, value):
        node = self._kv.get(key, None)
        if node is None:
            node = _LruNode()
            node._key = key
            node._value = value
            self._kv[key] = node
        else:
            node.remove_from_list()
            node._value = value
        node.insert_after(self._head)
        if len(self._kv) > self._cap:
            del_node = self._tail._prev.remove_from_list()
            del self._kv[del_node._key]

    def __getitem__(self, key):
        node = self._kv.get(key, None)
        if node is not None:
            node.remove_from_list()
            node.insert_after(self._head)
        return node._value

    def __delitem__(self, key):
        node = self._kv.get(key, None)
        if node is not None:
            node.remove_from_list()
            del self._kv[node._key]


class LruDictR(LruDict):
    ''' Thread safe version '''
    def __init__(self, cap):
        super(LruDictR, self).__init__(cap)
        self._lock = threading.Lock()

    def __setitem__(self, key, value):
        with self._lock:
            return super(LruDictR, self).__setitem__(key, value)

    def __getitem__(self, key):
        with self._lock:
            return super(LruDictR, self).__getitem__(key)

    def __delitem__(self, key):
        with self._lock:
            return super(LruDictR, self).__delitem__(key)


if '__main__' == __name__:
    import sys
    def print_dict(d):
        node = d._head._next
        print('{')
        while node and node != d._tail:
            print('  {0}: {1}'.format(node._key, node._value))
            node = node._next
        print('}')

    ld = LruDict(2)
    for i in iter_range(10000):
        ld['key{0}'.format(i)] = i
