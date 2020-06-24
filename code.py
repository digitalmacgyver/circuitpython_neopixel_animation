import time
import board
import analogio
import digitalio
import neopixel
import supervisor


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

    This animation simulates a light source moving along a path, with
    the LEDs being reflectors or readings of the intensity of that
    light source as it moves by.

    The model is that the light source:

    * Moves at the velocity "speed" along the "path_length"
    * The light source is visible for "lead" units of distance ahead of the light source
    * And "trail" units behind
    * As distance grows from the light source the intensity diminishes according to our attenuation() function
    * The readings of light intensity are made at the locations specified in light_ps
    * The path of the light source is cyclic, arriving at 0 as soon as it passes path_length

    The simulation provides the above constants, as well as the
    current time, this function returns the intensity of light along
    the path at that time.

    '''

    # Helper function.
    def attenuate( a, peak ):
        return ( int( a*peak[0] ), int( a*peak[1] ), int( a*peak[2] ) )

    # Prepare return value of light intensity values.
    light_vs = []
    for i in range( len( light_ps ) ):
        light_vs.append( ( 0, 0, 0 ) )

    # Get the current position of the light source.
    pos = speed*time
    while pos > path_length:
        pos -= path_length

    # Compute the intensity at each of the sensor light_ps.
    for i in range( len( light_ps ) ):
        # Position of the current sensor.
        light_p = light_ps[i]
        # Intensity of the current sensor
        light_v = light_vs[i]

        # Handle cases where we might be in the trailing illuminated
        # section.
        if light_p < pos - trail:
            # Outside the visible trailing distance.

            # Set to off.
            #print( "Turning light off" )
            light_v = ( 0, 0, 0 )
        elif light_p < pos:
            # Within the visible trailing distance.

            a = attenuation( pos - light_p, trail )
            light_v = attenuate( a, peak )
            #print( "Set light to:" )
            #print( light_v )
        elif trail > pos and light_p >= path_length - trail + pos:
            # Within the visible trailing distance, but the sensor is
            # towards the end of the circular path and the light
            # source is towards the begining.
            a = attenuation( path_length - light_p + pos, trail )
            light_v = attenuate( a, peak )
            #print( "Set light to:" )
            #print( light_v )

        # Handle cases where we might be in the leading illuminated
        # section.
        if light_p > pos and light_p < pos + lead:
            a = attenuation( light_p - pos, lead )
            light_v = attenuate( a, peak )
        elif pos + lead > path_length and light_p < pos + lead - path_length:
            a = attenuation( light_p + path_length - pos, lead )
            light_v = attenuate( a, peak )

        light_vs[i] = light_v


    #print( "Returning: %s" % ( light_vs ) )
    return light_vs

# Helper function to get the positions of n evenly spaced lights on a
# circular path.
def get_light_ps( path_length, n ):
    light_ps = [ 0 ]
    for i in range( 1, n ):
        light_ps.append( i * path_length / n )
    return light_ps


def rainbow( pos ):
    # Input a value 0 to 255 to get a color value that cycles from r to g to b.
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
    # Controlling the pixels on the board.
    #pixel_pin = board.NEOPIXEL

    # Controlling the LED strip attached to A1.
    # DEBUG - one of these is wrong, not sure which...
    # A
    #pixel_pin = digitalio.DigitalInOut( board.A0 )
    #pixel_pin.direction = digitalio.Direction.OUTPUT
    # B
    pixel_pin = board.A0
    #
    # DEBUG - when I figure out which it is, use the other to control
    # the circular LED lights.
    circle_pin = board.A1

    # Code for digital switches
    button_1 = digitalio.DigitalInOut( board.A2 )
    button_1.direction = digitalio.Direction.INPUT
    button_1.pull = digitalio.Pull.UP

    button_2 = digitalio.DigitalInOut( board.A3 )
    button_2.direction = digitalio.Direction.INPUT
    button_2.pull = digitalio.Pull.UP

    button_3 = digitalio.DigitalInOut( board.A4 )
    button_3.direction = digitalio.Direction.INPUT
    button_3.pull = digitalio.Pull.UP

    button_4 = digitalio.DigitalInOut( board.A5 )
    button_4.direction = digitalio.Direction.INPUT
    button_4.pull = digitalio.Pull.UP

    # Set up our Circle Pixels
    #
    # DEBUG - for the circle pixels we just want them always on doing
    # rainbow stuff.
    num_circle_pixels = 16
    circle_pixels = neopixel.NeoPixel( circle_pin, num_circle_pixels, brightness=1.0, auto_write=False )
    for i in range( len( circle_pixels ) ):
        circle_pixels[i] = ( 0, 0, 0 )

    circle_path_length = 30
    circle_speed = 11
    circle_trail = 30
    circle_lead = 0

    circle_ps = get_light_ps( circle_path_length, num_circle_pixels )

    # Set up our LED strip
    num_pixels = 28
    pixels = neopixel.NeoPixel( pixel_pin, num_pixels, brightness=1.0, auto_write=False )
    for i in range( len( pixels ) ):
        pixels[i] = ( 0, 0, 0 )
    zero_pixels = [ ( 0, 0, 0 ), ( 0, 0, 0 ), ( 0, 0, 0 ), ( 0, 0, 0 ), ( 0, 0, 0 ), ( 0, 0, 0 ), ( 0, 0, 0 ) ]

    # Overall model properties for our light.
    path_length = 30
    speed = 24
    trail = 7
    lead = 1.5

    # Light positions for segment 1, and for segment 2, 3, 4.
    #
    # Segments 2, 3, 4 are arranged this way so as to make the
    # animation of the light flow smoothly from segment 1 into the
    # other segments.
    light_ps_1 = [ 0, 3, 6, 9, 12, 15, 18 ]
    light_ps_234 = [ 21, 24, 27, 0, 3, 6, 9 ]

    # The current time used by the animation model, and the interval
    # in time between updates in the model.
    t = 0
    interval = 3/100

    # Establish the initial colors of each of the four ranges to a
    # different spot in the RGB rainbow cycle.
    color_a = 0*(256/4)
    color_b = 1*(256/4)
    color_c = 2*(256/4)
    color_d = 3*(256/4)

    # Loop forever.
    reset_count = 0
    while True:
        # The system locks up after a while - try to hard reboot it around 10 hours in.
        reset_count += 1
        if reset_count > 1000000:
            reset_count = 0
            supervisor.reload()

        # Determine what we need to animate, the rules are:
        # button_1 -> LED segment 1 is
        # button_1 && button_2 -> Segment 2
        # button_1 && button_2 && button_3 -> Segment 3
        # button_1 && button_2 && button_4 -> Segment 4
        # button_1 && button_2 && button_3 && button_4 -> Circle

        # Set up the colors for the light source on each of the four
        # segments.
        peak_a = rainbow( color_a )
        peak_b = rainbow( color_b )
        peak_c = rainbow( color_c )
        peak_d = rainbow( color_d )

        # Update colors for next iteration.
        color_a += 1
        color_a = color_a % 256
        color_b += 1
        color_b = color_b % 256
        color_c += 1
        color_c = color_c % 256
        color_d += 1
        color_d = color_d % 256

        #print( "Buttons: ", [ button_1.value, button_2.value, button_3.value, button_4.value ] )

        button_override = True

        # Light up the appropriate pixels.
        #
        # Switches are active when they read as false.
        tmp = zero_pixels
        if button_override or not button_1.value:
            tmp = animate_path( path_length, speed, trail, lead, light_ps_1, t, peak=peak_a )
        for i in range( len( tmp ) ):
            pixels[i] = tmp[i]

        tmp = zero_pixels
        if button_override or ( not button_1.value and not button_2.value ):
            tmp = animate_path( path_length, speed, trail, lead, light_ps_234, t, peak=peak_b )
        for i in range( len( tmp ) ):
            pixels[7+i] = tmp[i]

        tmp = zero_pixels
        if button_override or ( not button_1.value and not button_2.value and not button_3.value ):
            tmp = animate_path( path_length, speed, trail, lead, light_ps_234, t, peak=peak_c )
        for i in range( len( tmp ) ):
            pixels[14+i] = tmp[i]

        tmp = zero_pixels
        if button_override or ( not button_1.value and not button_2.value and not button_4.value ):
            tmp = animate_path( path_length, speed, trail, lead, light_ps_234, t, peak=peak_d )
        for i in range( len( tmp ) ):
            pixels[21+i] = tmp[i]

        if button_override or ( not button_1.value and not button_2.value and not button_3.value and not button_4.value ):
            #circle_tmp = animate_path( circle_path_length, circle_speed, circle_trail, circle_lead, circle_ps, t, peak=peak_a )
            for i in range( len( circle_pixels ) ):
                circle_pixels[i] = rainbow( 255 & int( ( i*256 / num_circle_pixels ) + color_a*10 ) )
        else:
            for i in range( len( circle_pixels ) ):
                circle_pixels[i] = ( 0, 0, 0 )



        #print( pixels )
        pixels.show()
        circle_pixels.show()
        time.sleep( interval )
        t += interval
        #print( t )
        if t > path_length / speed:
            t -= path_length / speed

print( "Starting" )
# There seems to be intermittent failures which are eased by a delay here.
time.sleep(2)
driver()

