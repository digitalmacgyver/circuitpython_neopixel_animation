import time
import board
import analogio
import digitalio
import neopixel

# Possible attenuation modes.
LINEAR = 'linear'

def attenuation( distance, width, method=LINEAR ):
    if distance > width:
        raise Exception( "Distance must be lte width." )
    if method != LINEAR:
        raise Exception( "Method: %s not supported." % ( method ) )
    else:
        return 1 - distance / width

def animate_path( path_length, speed, trail, lead, light_ps, time, peak=( 255, 255, 255 ) ):
    '''Given the above parameters, returns an intensity for each light in
    an array of tuples format.

    '''

    #print( "Here 1" )

    # Helper function.
    def attenuate( a, peak ):
        return ( int( a*peak[0] ), int( a*peak[1] ), int( a*peak[2] ) )

    #print( "Here 2" )

    # Prepare return value.
    light_vs = []
    for i in range( len( light_ps ) ):
        light_vs.append( ( 0, 0, 0 ) )

    #print( "Here 3" )

    pos = speed*time
    while pos > path_length:
        pos -= path_length

    #print( "Here 4" )

    for i in range( len( light_ps ) ):
        #print( "Here 5:%d" % ( i ) )

        light_p = light_ps[i]
        light_v = light_vs[i]

        # Handle trailing.
        if light_p < pos - trail:
            # Set to off.
            #print( "Turning light off" )
            light_v = ( 0, 0, 0 )
        elif light_p < pos:
            a = attenuation( pos - light_p, trail )
            light_v = attenuate( a, peak )
            #print( "Set light to:" )
            #print( light_v )
        elif trail > pos and light_p >= path_length - trail + pos:
            a = attenuation( path_length - light_p + pos, trail )
            light_v = attenuate( a, peak )
            #print( "Set light to:" )
            #print( light_v )

        # Handle leading
        if light_p > pos and light_p < pos + lead:
            # Set to off.
            #print( "Turning light off" )
            a = attenuation( light_p - pos, lead )
            light_v = attenuate( a, peak )
        elif pos + lead > path_length and light_p < pos + lead - path_length:
            a = attenuation( light_p + path_length - pos, lead )
            light_v = attenuate( a, peak )

        light_vs[i] = light_v


    #print( "Returning: %s" % ( light_vs ) )
    return light_vs

# Helper function to get the positions of n evenly spaced lights on
# our circular path.
def get_light_ps( path_length, n ):
    light_ps = [ 0 ]
    for i in range( 1, n ):
        light_ps.append( i * path_length / n )
    return light_ps


def wheel( pos ):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)//5
        g = int(255 - pos*3)//5
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos*3)//5
        g = 0
        b = int(pos*3)//5
    else:
        pos -= 170
        r = 0
        g = int(pos*3)//5
        b = int(255 - pos*3)//5
    return (r, g, b)

def driver():
    #pixel_pin = board.NEOPIXEL
    #pixel_pin = digitalio.DigitalInOut( board.A1 )
    #pixel_pin.direction = digitalio.Direction.OUTPUT

    button_1 = analogio.AnalogIn( board.A3 )

    pixel_pin = board.A2
    num_pixels = 28
    pixels = neopixel.NeoPixel( pixel_pin, num_pixels, brightness=0.5, auto_write=False )

    n = 7
    path_length = 30
    speed = 24
    trail = 7
    lead = 1.5
    light_ps_1 = [ 0, 3, 6, 9, 12, 15, 18 ]
    light_ps_234 = [ 21, 24, 27, 0, 3, 6, 9 ]
    #light_ps = get_light_ps( path_length, n )

    # Create our 4 pixel ranges.
    off_a = 0
    off_b = 7
    off_c = 14
    off_d = 21
    pa = pixels[off_a:n+off_a-1]
    pb = pixels[off_b:n+off_b-1]
    pc = pixels[off_c:n+off_c-1]
    pd = pixels[off_d:n+off_d-1]

    #light_ps = [ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9 ]
    #light_ps = [ 0, .25, .75, 1.75, 3, 4, 4.5, 4.75, 5, 5.25 ]
    t = 0
    # time.monotoic() to get floating point seconds - can use if loop processing takes a long time relative to interval
    interval = 3/100

    #print( light_ps )

    color_a = 0*(256/4)
    color_b = 1*(256/4)
    color_c = 2*(256/4)
    color_d = 3*(256/4)

    cycle = 0

    while True:
        peak_a = wheel( color_a )
        peak_b = wheel( color_b )
        peak_c = wheel( color_c )
        peak_d = wheel( color_d )

        color_a += 1
        color_a = color_a % 256
        color_b += 1
        color_b = color_b % 256
        color_c += 1
        color_c = color_c % 256
        color_d += 1
        color_d = color_d % 256

        light_vs_abcd = animate_path( path_length, speed, trail, lead, light_ps_1, t, peak=peak_a ) + animate_path( path_length, speed, trail, lead, light_ps_234, t, peak=peak_b )+ animate_path( path_length, speed, trail, lead, light_ps_234, t, peak=peak_c ) + animate_path( path_length, speed, trail, lead, light_ps_234, t, peak=peak_d )

        # We want to iterate among region: 1, 1+2, 1+2+3, 1+2+3+4
        for i in range( off_a, off_a + n  ):
            pixels[i] = light_vs_abcd[i]
        if cycle > 1 or ( cycle == 1 and lead+t*speed >= light_ps_234[0] ):
            for i in range( off_b, off_b + n  ):
                pixels[i] = light_vs_abcd[i]
        else:
            for i in range( off_b, off_b + n  ):
                pixels[i] = ( 0, 0, 0 )
        if cycle > 2 or ( cycle == 2 and lead+t*speed >= light_ps_234[0] ):
            for i in range( off_c, off_c + n  ):
                pixels[i] = light_vs_abcd[i]
        else:
            for i in range( off_c, off_c + n  ):
                pixels[i] = ( 0, 0, 0 )
        if cycle > 3 or ( cycle == 3 and lead+t*speed >= light_ps_234[0] ):
            for i in range( off_d, off_d + n  ):
                pixels[i] = light_vs_abcd[i]
        else:
            for i in range( off_d, off_d + n  ):
                pixels[i] = ( 0, 0, 0 )

        #print( pixels )
        print( button_1.value )
        if button_1.value > 500:
            for i in range( num_pixels ):
                pixels[i] = ( 0, 0, 0 )
        pixels.show()
        time.sleep( interval )
        t += interval
        #print( t )
        if t > path_length / speed:
            cycle += 1
            # Give us three full cycles at everything lit up before starting over.
            cycle = cycle % 7
            t -= path_length / speed
            #t = 0

def led_driver():
    led = digitalio.DigitalInOut( board.D13 )
    led.direction = digitalio.Direction.OUTPUT
    
    #button = digitalio.DigitalInOut( board.BUTTON_A )
    #button.direction = digitalio.Direction.INPUT
    #button.pull = digitalio.Pull.DOWN
    
    button = analogio.AnalogIn( board.A3 )
    #button.direction = analogio.Direction.INPUT
    #button.pull = analogio.Pull.DOWN

    
    while True:
        if button.value < 1000:
            print( button.value )
            led.value = True
        else:
            led.value = False
        time.sleep( 0.05 )

print( "Starting" )
driver()
#led_driver()
