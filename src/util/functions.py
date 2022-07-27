import functools
import numpy as np
    
def _g(N, M, x):
    if N == M:
        return x,x
    elif N > M:
        return (x*M) // N, (x*M) // N
    elif N < M:
        l = (x * M) // N if (x * M) % N == 0 else (x * M) // N + 1
        u = ((x+1) * M) // N - 1 if ((x+1) * M) % N == 0 else ((x+1) * M) // N
        return l,u
    else:
        raise ValueError    

# annahme N > M 
def get_translation_array(N, M):
    arr = np.zeros((N,2), int)
    for idx in range(N):
        arr[idx][0] = idx
        arr[idx][1] = (idx * M) // N
    return arr

def _h(arr, inverse, x):
    if inverse:
        idx = 0
        while(arr[idx][1] != x):
            idx += 1
        l = arr[idx][0]
        while(idx < len(arr) and arr[idx][1] == x):
            u = arr[idx][0]
            idx += 1
    else:  
        idx = 0
        while(arr[idx][0] != x):
            idx += 1
        l = arr[idx][1]
        while(idx < len(arr) and arr[idx][0] == x):
            u = arr[idx][1]
            idx += 1
    return l, u

def _scale(N, M):
    if N > M:
        arr = get_translation_array(N, M) # N -> M
        n2m = functools.partial(_h, arr, False)
        m2n = functools.partial(_h, arr, True)
    elif N < M:
        arr = get_translation_array(M, N) # M -> N
        n2m = functools.partial(_h, arr, True)
        m2n = functools.partial(_h, arr, False)
    else:
        n2m, m2n = lambda x: x, lambda x: x
        
    return n2m, m2n

def scale_functions(N: int, M: int, last_to_last: bool = False):
    """ create scaling functions

    Args:
        N (int): Number of elements in the first range.
        M (int): Number of elements in the second range.
        last_to_last (bool, optional): Sometimes its usefull if the last elements of two ranges always map to each other. Defaults to False.

    Returns:
        n2m: function: Map from n to m.
        m2n: function. Map from m to n.
    """
    offset = int(last_to_last) if N > 1 and M > 1 else 0
    n2m = functools.partial(_g, N - offset, M - offset)
    m2n = functools.partial(_g, M - offset, N - offset)

    return n2m, m2n


def ms_to_time_string(ms):
        mins = ms // (60*1000)
        ms %= (60*1000)
        secs = ms // 1000
        ms %= 1000
        return '{:02d}:{:02d}:{:03d}'.format(mins, secs, ms)
    