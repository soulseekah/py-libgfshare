import ctypes
import random
from ctypes import *

random.seed( None )

class GFShareContext( Structure ):
	_fields_ = \
		[
			( 'sharecount', c_uint ),
			( 'threshold', c_uint ),
			( 'size', c_uint ),
			( 'sharenrs', POINTER( c_ubyte ) ),
			( 'buffer', POINTER( c_ubyte ) ),
			( 'buffersize', c_uint ),
		]

libgfshare = ctypes.cdll.LoadLibrary( 'libgfshare.so' )

libgfshare.gfshare_ctx_init_enc.argtypes = \
	[ POINTER( c_ubyte ), c_uint, c_ubyte, c_uint ]
libgfshare.gfshare_ctx_init_enc.restype = POINTER( GFShareContext )

libgfshare.gfshare_ctx_enc_setsecret.argtypes = \
	[ POINTER( GFShareContext ), POINTER( c_ubyte ) ]

libgfshare.gfshare_ctx_enc_getshare.argtypes = \
	[ POINTER( GFShareContext ), c_ubyte, POINTER( c_ubyte ) ]

libgfshare.gfshare_ctx_init_dec.argtypes = \
	[ POINTER( c_ubyte ), c_uint, c_uint ]
libgfshare.gfshare_ctx_init_dec.restype = POINTER( GFShareContext )

libgfshare.gfshare_ctx_dec_giveshare.argtypes = \
	[ POINTER( GFShareContext ), c_ubyte, POINTER( c_ubyte ) ]

libgfshare.gfshare_ctx_dec_extract.argtypes = \
	[ POINTER( GFShareContext ), POINTER( c_ubyte ) ]

libgfshare.gfshare_ctx_free.argtypes = [ POINTER( GFShareContext ) ]


def _fill_random( buffer, count ):
	""" By default libgfshare uses the libc random() function to fill the
	buffer with random data. This is not ideal, so we have to provide a
	much better and secure implementation.
	
	As an example this implementation uses Python's random library. Feel
	free to redefine this function as it offers little to no advantage over
	the internal implementation.

	A better but slow implementation would use /dev/random, for example.
	"""

	for x in range( count ):
		buffer[x] = random.randint( 0, 255 )

def split( sharecount, threshold, data ):
	""" Split `data` into `sharecount` shares, with any `threshold`
	shares required for recombination. Returns a list of tuples:
		[
			( sharenr, data ),
			( sharenr, data ),
			...
		]
	
	Note: the `data` is not destroyed or cleared from memory, this is
	left up to the client to do after calling the function. Keep your memory
	safe.
	"""

	if sharecount > 255:
		raise ValueError( 'Amount of shares cannot be larger than 255 as we are working in GF(2**8)' )
	if sharecount < 2:
		raise ValueError( 'Amount of shares cannot be less than 2, they are called shares for a reason' )
	if threshold > sharecount:
		raise ValueError( 'Threshold cannot be more than the amount of shares' )
	if threshold < 2 :
		raise ValueError( 'Threshold cannot be less than 2, single shares do not contain enough information' )

	# Set the fill_random callback
	fill_random = CFUNCTYPE( None, POINTER( c_ubyte ), c_uint )( _fill_random )
	gfshare_fill_rand = c_void_p.in_dll( libgfshare, 'gfshare_fill_rand' )
	gfshare_fill_rand.value = cast( fill_random, c_void_p ).value

	# Generate the needed unique share numbers at random
	sharenrs = random.sample( range( 1, 256 ), sharecount )
	sharenrs = list( map( lambda x: c_ubyte( x ), sharenrs ) )
	sharenrs = ( c_ubyte * len( sharenrs ) )( *sharenrs )

	# Setup the context
	ctx = libgfshare.gfshare_ctx_init_enc( \
		sharenrs, c_uint( sharecount ), c_ubyte( threshold ), c_uint( len( data ) ) )
	
	data = list( map( lambda x: ord( x ), data ) )
	data = ( c_ubyte * len( data ) )( *data )

	libgfshare.gfshare_ctx_enc_setsecret( ctx, data )

	shares = []

	# Retrieve the shares
	for sharenr in range( sharecount ):
		share = ( c_ubyte * len( data ) )()
		libgfshare.gfshare_ctx_enc_getshare( ctx, sharenr, share )
		shares.append( ( sharenrs[sharenr], ''.join( list( map( lambda x: chr( x ), share ) ) ) ) )
	
	libgfshare.gfshare_ctx_free( ctx )
	
	return shares

def combine( shares ):
	""" Combine `shares` back into the secret. Expects a list of tuples:
		[
			( sharenr, data ),
			( sharenr, data ),
			...
		]
	
	Make sure to wipe the memory after you get the secret.
	"""

	if len( shares ) > 255:
		raise ValueError( 'There can never be more than 255 shares as we are working in GF(2**8)' )
	if len( shares ) < 2:
		raise ValueError( 'There has to be at least 2 shares to reconstruct the secret' )

	sharenrs = list( map( lambda x: x[0], shares ) )
	sharenrs = list( map( lambda x: c_ubyte( x ), sharenrs ) )
	sharenrs = ( c_ubyte * len( sharenrs ) )( *sharenrs )

	size = len( shares[0][1] )
	for share in shares:
		if len( share[1] ) != size:
			raise ValueError( 'Shares are not of the same size, cannot mix and match' )

	# Setup the context
	ctx = libgfshare.gfshare_ctx_init_dec( \
		sharenrs, c_uint( len( shares ) ), c_uint( size ) )

	# Recombine the shares
	for sharenr, share in enumerate( shares ):

		_, share = share

		share = list( map( lambda x: ord( x ), share ) )
		share = ( c_ubyte * size )( *share )

		libgfshare.gfshare_ctx_dec_giveshare( ctx, sharenr, share )
	
	secret = ( c_ubyte * size )()
	libgfshare.gfshare_ctx_dec_extract( ctx, secret )

	libgfshare.gfshare_ctx_free( ctx )

	return ''.join( list( map( lambda x: chr( x ), secret ) ) )
