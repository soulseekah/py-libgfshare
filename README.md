py-libgfshare
=============

A Python ctypes wrapper for libgfshare - http://www.digital-scurf.org/software/libgfshare (download, `./configure`, `make`, `make install` or `cp .libs/libgfshare.so /usr/lib/`)

Shamir's method for secret sharing in the Galois Field 2^8. http://en.wikipedia.org/wiki/Shamir's_Secret_Sharing

**Usage**:

    import gfshare
    shares = gfshare.split( 7, 2, 'Hello World!' )
    gfshare.combine( ( shares[5], shares[2] ) )
    gfshare.combine( ( shares[1], shares[6] ) )

Tested on Python 2.7.4 and Python 3.3.1

Current `gfshare._fill_random` implementation uses Python's `random` library. It is recommended to reimplement the function yourself more securely (using `/dev/random` for example).

Todo:
- Wrap new share recombination functionality
- Add Windows and OSX support
- Add setup.py and all the usual goodies
- Simpler `_fill_random` interface, to avoid using `ctypes` in client

Code comes without any warranty of any sorts. Bug reports and contributions more than welcome.
