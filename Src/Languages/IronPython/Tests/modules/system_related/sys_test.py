#####################################################################################
#
#  Copyright (c) Microsoft Corporation. All rights reserved.
#
# This source code is subject to terms and conditions of the Microsoft Public License. A
# copy of the license can be found in the License.html file at the root of this distribution. If
# you cannot locate the  Microsoft Public License, please send an email to
# ironpy@microsoft.com. By using this source code in any fashion, you are agreeing to be bound
# by the terms of the Microsoft Public License.
#
# You must not remove this notice, or any other, from this software.
#
#
#####################################################################################

from iptest.assert_util import *

# adding some negative test case coverage for the sys module; we currently don't implement
# some methods---there is a CodePlex work item 1042 to track the real implementation of
# these methods

import sys

@skip("win32")
def test_dont_write_bytecode():
    AreEqual(sys.dont_write_bytecode, True)

def test_getframe():
    # This test requires -X:FullFrames, run it in separate instance of IronPython.
    global testDelGetFrame
    if not testDelGetFrame:
        return

    _getframe = sys._getframe

    for val in [None, 0, 1L, str, False]:
        sys._getframe = val
        AreEqual(sys._getframe, val)

    del sys._getframe
    
    try:
        # try access again
        x = sys._getframe
    except AttributeError: pass
    else: raise AssertionError("Deletion of sys._getframe didn't take effect")
    
    try:
        # try deletion again
        del sys._getframe
    except AttributeError: pass
    else: raise AssertionError("Deletion of sys._getframe didn't take effect")
    
    # restore it back
    sys._getframe = _getframe

    def g():
        y = 42
        def f():
            x = sys._getframe(1)
            return x

        AreEqual(f().f_locals['y'], 42)
        Assert(f().f_builtins is f().f_globals['__builtins__'].__dict__)
        AreEqual(f().f_locals['y'], 42)
        AreEqual(f().f_exc_traceback, None)
        AreEqual(f().f_exc_type, None)
        AreEqual(f().f_restricted, False)
        AreEqual(f().f_trace, None)

        # replace __builtins__, func code should have the non-replaced value
        global __builtins__
        oldbuiltin = __builtins__
        try:
            __builtins__ = dict(__builtins__.__dict__)
            def f():
                x = sys._getframe(1)
                return x
            Assert(f().f_builtins is oldbuiltin.__dict__)
        finally:
            __builtins__ = oldbuiltin

        def f():
            x = sys._getframe()
            return x

        AreEqual(f().f_back.f_locals['y'], 42)

        def f():
            yield sys._getframe()
           
        frame = list(f())[0]
        if is_cli:
            # incompat, this works for us, but not CPython, not sure why.
            AreEqual(frame.f_back.f_locals['y'], 42)
        
        # call through a built-in function
        global gfres
        class x(object):
            def __cmp__(self, other):
                global gfres
                gfres = sys._getframe(1)
                return -1
                
        cmp(x(), x())
        AreEqual(gfres.f_locals['y'], 42)
    g()
    
    def f():
        x = 42
        def g():
                import sys
                AreEqual(sys._getframe(1).f_locals['x'], 42)
        g()
        yield 42
    
    list(f())
    
    class x:
        abc = sys._getframe(0)
        
    AreEqual(x.abc.f_locals['abc'], x.abc)
    
    class x:
        class y:
            abc = sys._getframe(1)
        abc = y.abc
    
    AreEqual(x.abc.f_locals['abc'], x.abc)

    for i in xrange(2):
        x = _getframe(0)
        y = _getframe(0)
        AreEqual(id(x), id(y))
    

    # odd func_code tests which require on _getframe
    global get_odd_code
    def get_odd_code():
        c = sys._getframe(1)
        return c.f_code
    
    def verify(code, is_defined):
        d = { 'get_odd_code' : get_odd_code }
        exec code in d
        AreEqual('defined' in d, is_defined)

    class x(object):
        abc = get_odd_code()
        defined = 42

    verify(x.abc, False)
    
    class x(object):
        abc = get_odd_code()
        global defined
        defined = 42

    if is_cli: # bug 20553 http://ironpython.codeplex.com/WorkItem/View.aspx?WorkItemId=20553
        verify(x.abc, False)
    else:
        verify(x.abc, True)

    d = {'get_odd_code' : get_odd_code}
    exec 'defined=42\nabc = get_odd_code()\n' in d
    verify(d['abc'], True)
    
    # bug 24243, code objects should never be null
    class x(object):
        f = sys._getframe()
        while f:
            Assert(f.f_code is not None)
            Assert(f.f_code.co_name is not None)
            f = f.f_back

    # bug 24313, sys._getframe should return the same frame objects
    # that tracing functions receive
    def method():
        global method_id
        method_id = id(sys._getframe())

    def trace_dispatch(frame, event, arg):
        global found_id
        found_id = id(frame)

    sys.settrace(trace_dispatch)
    method()
    sys.settrace(None)
    
    AreEqual(method_id, found_id)

    # verify thread safety of sys.settrace
    import thread
    import time
    global done
    done = 0
    lock = thread.allocate_lock()
    def starter(events):
        def tracer(*args):
            events.append(args[1])
            return tracer
        def f1(): time.sleep(.25)
        def f2(): time.sleep(1)
        def f3(): time.sleep(.5)
        
        def test_thread():
            global done
            sys.settrace(tracer)
            f1()
            sys.settrace(None)
            f2()
            sys.settrace(tracer)
            f3()
            with lock: done += 1
            
        thread.start_new_thread(test_thread, ())
    
    lists = []
    for i in xrange(10):
        cur_list = []
        starter(cur_list)
        lists.append(cur_list)
    
    while done != 10:
       pass    
    for i in xrange(1, 10):
        AreEqual(lists[i-1], lists[i])

    # verify we report <module> for top-level code
    frame = sys._getframe()
    outer_frame = frame.f_back
    while outer_frame is not None:
        frame = outer_frame
        outer_frame = frame.f_back
    AreEqual(frame.f_code.co_name, "<module>")


@skip("win32")
def test_api_version():
    # api_version
    AreEqual(sys.api_version, 0)

@skip("silverlight")
def test_settrace():
    """TODO: now that sys.settrace has been implemented this test case needs to be fully revisited"""
    # settrace
    Assert(hasattr(sys, 'settrace'))
    
    global traces
    traces = []
    def f(frame, kind, info):
        traces.append(('f', kind, frame.f_code.co_name))
        return g

    def g(frame, kind, info):
        traces.append(('g', kind, frame.f_code.co_name))
        return g_ret

    g_ret = g
    def x():
        abc = 'hello'
        abc = 'next'

    sys.settrace(f)
    x()
    sys.settrace(None)
    AreEqual(traces, [('f', 'call', 'x'), ('g', 'line', 'x'), ('g', 'line', 'x'), ('g', 'return', 'x')])

    traces = []
    g_ret = f
    sys.settrace(f)
    x()
    sys.settrace(None)
    AreEqual(traces, [('f', 'call', 'x'), ('g', 'line', 'x'), ('f', 'line', 'x'), ('g', 'return', 'x')])
    
    # verify globals/locals are correct on the frame
    global frameobj
    def f(frame, event, payload):
        global frameobj
        frameobj = frame
    
    def g(a):
        b = 42
        
    sys.settrace(f)    
    g(32)
    sys.settrace(None)
    AreEqual(frameobj.f_locals, {'a': 32, 'b':42})
    Assert('test_getrefcount' in frameobj.f_globals)
    
    if is_cli:
        # -X:Tracing should enable tracing of top-level code
        import os
        content = """a = "aaa"
import pdb; pdb.set_trace()
b = "bbb"
c = "ccc"
final = a + b + c
print final"""
        f = file('temp.py', 'w+')
        try:
            f.write(content)
            f.close()
            
            stdin, stdout = os.popen2(sys.executable +  ' -X:Tracing -X:Frames temp.py')
            stdin.write('n\nn\nn\nn\nn\nn\nn\nn\n')
            stdin.flush()
            out = [x for x in stdout]
            Assert('-> b = "bbb"\n' in out)
            Assert('-> c = "ccc"\n' in out)
            Assert('-> final = a + b + c\n' in out)
            Assert('-> print final\n' in out)
            Assert('(Pdb) aaabbbccc\n' in out)
            Assert('--Return--\n' in out)
            Assert('-> print final\n' in out)
            Assert('(Pdb) ' in out)
        finally:
            nt.unlink('temp.py')


@skip("win32")
def test_getrefcount():
    # getrefcount
    Assert(not hasattr(sys, 'getrefcount'))

@skip("win32 silverlight")
def test_version():
    import re
    #E.g., 2.5.0 (IronPython 2.0 Alpha (2.0.0.800) on .NET 2.0.50727.1433)
    regex = "^\d\.\d\.\d \(IronPython \d\.\d(\.\d)? ((Alpha \d+ )|(Beta \d+ )|())((DEBUG )|()|(\d?))\(\d\.\d\.\d{1,8}\.\d{1,8}\) on \.NET \d(\.\d{1,5}){3}\)$"
    Assert(re.match(regex, sys.version) != None)

def test_winver():
    import re
    #E.g., "2.5"
    Assert(re.match("^\d\.\d$", sys.winver) != None)

def test_ps1():
    Assert(not hasattr(sys, "ps1"))

def test_ps2():
    Assert(not hasattr(sys, "ps2"))    

@skip("silverlight")
def test_getsizeof():
    '''TODO: revisit'''
    if is_cpython:
        Assert(sys.getsizeof(1)<sys.getsizeof(1.0))
    else:
        AreEqual(sys.getsizeof(1), sys.getsizeof(1.0))

@skip("silverlight")
def test_gettrace():
    '''TODO: revisit'''
    AreEqual(sys.gettrace(), None)
    
    def temp_func(*args, **kwargs):
        pass
        
    sys.settrace(temp_func)
    AreEqual(sys.gettrace(), temp_func)
    sys.settrace(None)
    AreEqual(sys.gettrace(), None)

@skip("silverlight")
def test_cp24242():
    # This test requires -X:FullFrames, run it in separate instance of IronPython.
    global testDelGetFrame
    if not testDelGetFrame:
        return
        
    frame = sys._getframe()
    ids = []
    while frame:
        ids.append(id(frame))
        frame = frame.f_back
    del frame
    force_gc()

    frame = sys._getframe()
    new_ids = []
    while frame:
        new_ids.append(id(frame))
        frame = frame.f_back
    del frame
    force_gc()
    
    AreEqual(ids, new_ids)


CP24381_MESSAGES = []
@skip("silverlight", "cli")
def test_cp24381():
    import sys
    orig_sys_trace_func = sys.gettrace()
    def f(*args):
        global CP24381_MESSAGES
        CP24381_MESSAGES += args[1:]
        return f
    
    cp24381_file_name = r"cp24381.py"
    cp24381_contents  = """
print 'a'
print 'b'
print 'c'

def f():
    print 'hi'

f()
"""

    try:
        write_to_file(cp24381_file_name, cp24381_contents)
        sys.settrace(f)
        import cp24381
    finally:
        sys.settrace(orig_sys_trace_func)
        nt.unlink(cp24381_file_name)

    AreEqual(CP24381_MESSAGES,
             ['call', None, 'line', None, 'line', None, 'line', None, 'line', 
              None, 'line', None, 'call', None, 'line', None, 'return', None, 
              'return', None])

#--MAIN------------------------------------------------------------------------    

testDelGetFrame = "Test_GetFrame" in sys.argv
if testDelGetFrame:
    print 'Calling test_getframe()...'
    test_getframe()
    print 'Calling test_cp24242()...'
    test_cp24242()
else:
    run_test(__name__)
    # this is a destructive test, run it in separate instance of IronPython
    if not is_silverlight and sys.platform!="win32":
        from iptest.process_util import launch_ironpython_changing_extensions
        AreEqual(0, launch_ironpython_changing_extensions(__file__, ["-X:FullFrames"], [], ("Test_GetFrame",)))
    elif sys.platform == "win32":
        print 'running test_getframe on cpython'
        import subprocess
        subprocess.check_call([sys.executable, __file__, "Test_GetFrame"])
        
