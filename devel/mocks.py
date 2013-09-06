from mock import Mock


# mock subprocess
subprocess = Mock()

def _dummy_popen(*args, **kwargs):
    print 'call to dummy popen:', args, kwargs
    mocked_return = Mock()
    mocked_return.pid = 1
    return mocked_return

subprocess.Popen = _dummy_popen