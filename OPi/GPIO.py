# -*- coding: utf-8 -*-
# Copyright (c) 2018 Richard Hull
# See LICENSE.md for details.

"""
Importing the module
--------------------
To import the OPi.GPIO module:

.. code:: python

   import OPi.GPIO as GPIO

By doing it this way, you can refer to it as just GPIO through the rest of your
script.

Pin Numbering
-------------
Pins on Orange Pi Zero are named PxNN where x = A..Z and NN = 00..99. This
implementation aims to paper over the cracks to make GPIO usage consistent
across Raspberry Pi and Orange Pi. Quoting from the RPi.GPIO documentation:

    *There are two ways of numbering the IO pins on a Raspberry Pi within
    RPi.GPIO. The first is using the BOARD numbering system. This refers to
    the pin numbers on the P1 header of the Raspberry Pi board. The advantage
    of using this numbering system is that your hardware will always work,
    regardless of the board revision of the RPi. You will not need to rewire
    your connector or change your code.*

    *The second numbering system is the BCM numbers. This is a lower level way
    of working - it refers to the channel numbers on the Broadcom SOC. You have
    to always work with a diagram of which channel number goes to which pin on
    the RPi board. Your script could break between revisions of Raspberry Pi
    boards.*

This library monkeys the original implementation (and the documentation, as you
are about to find out), by adding a third numbering system that is SUNXI naming.

.. image:: ../doc/images/OrangePi_Zero_Pinout_header.jpg

Inputs
------
There are several ways of getting GPIO input into your program. The first and
simplest way is to check the input value at a point in time. This is known as
'polling' and can potentially miss an input if your program reads the value at
the wrong time. Polling is performed in loops and can potentially be processor
intensive. The other way of responding to a GPIO input is using 'interrupts'
(edge detection). An edge is the name of a transition from HIGH to LOW (falling
edge) or LOW to HIGH (rising edge).

Pull up / Pull down resistors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. note:: Support for pull up / pull down resistors is not yet complete: if
   specified, a warning will be displayed instead, so that it is at least
   compatible with existing code, but without implemening the actual
   functionality.

If you do not have the input pin connected to anything, it will 'float'. In
other words, the value that is read in is undefined because it is not connected
to anything until you press a button or switch. It will probably change value a
lot as a result of receiving mains interference.

To get round this, we use a pull up or a pull down resistor. In this way, the
default value of the input can be set. It is possible to have pull up/down
resistors in hardware and using software. In hardware, a 10K resistor between
the input channel and 3.3V (pull-up) or 0V (pull-down) is commonly used. The
OPi.GPIO module allows you to configure the SOC to do this in software:

.. code:: python

   GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
     # or
   GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

(where channel is the channel number based on the numbering system you have
specified - BOARD, BCM or SUNXI).

Testing inputs (polling)
^^^^^^^^^^^^^^^^^^^^^^^^
You can take a snapshot of an input at a moment in time:

.. code:: python

   if GPIO.input(channel):
       print('Input was HIGH')
   else:
       print('Input was LOW')

To wait for a button press by polling in a loop:

.. code:: python

   while GPIO.input(channel) == GPIO.LOW:
       time.sleep(0.01)  # wait 10 ms to give CPU chance to do other things

(this assumes that pressing the button changes the input from LOW to HIGH)

Interrupts and Edge detection
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
An edge is the change in state of an electrical signal from LOW to HIGH (rising
edge) or from HIGH to LOW (falling edge). Quite often, we are more concerned by
a change in state of an input than it's value. This change in state is an event.

To avoid missing a button press while your program is busy doing something else,
there are two ways to get round this:

* the :py:func:`wait_for_edge` function
* the :py:func:`event_detected` function
* a threaded callback function that is run when an edge is detected

Threaded Callbacks
^^^^^^^^^^^^^^^^^^
OPi.GPIO manages a number of secondary threads for callback functions. This
means that callback functions can be run at the same time as your main program,
in immediate response to an edge.

For example:

.. code:: python

    def my_callback(channel):
        print('This is a edge event callback function!')
        print('Edge detected on channel %s'%channel)
        print('This is run in a different thread to your main program')

    GPIO.add_event_detect(channel, GPIO.RISING, callback=my_callback)  # add rising edge detection on a channel
    #...the rest of your program...

If you wanted more than one callback function:

.. code:: python

    def my_callback_one(channel):
        print('Callback one')

    def my_callback_two(channel):
        print('Callback two')

    GPIO.add_event_detect(channel, GPIO.RISING)
    GPIO.add_event_callback(channel, my_callback_one)
    GPIO.add_event_callback(channel, my_callback_two)

Note that in this case, the callback functions are run sequentially, not
concurrently. This is because there is only one thread used for callbacks, in
which every callback is run, in the order in which they have been defined.

Switch debounce
^^^^^^^^^^^^^^^
.. note:: Support for switch debounce is not yet complete: if specified, a
   warning will be displayed instead, so that it is at least compatible with
   existing code, but without implemening the actual functionality.

You may notice that the callbacks are called more than once for each button
press. This is as a result of what is known as 'switch bounce'. There are two
ways of dealing with switch bounce:

* add a 0.1µF capacitor across your switch.
* software debouncing
* a combination of both

To debounce using software, add the bouncetime= parameter to a function where
you specify a callback function. Bouncetime should be specified in milliseconds.
For example:

.. code:: python

   # add rising edge detection on a channel, ignoring further edges for 200ms for switch bounce handling
   GPIO.add_event_detect(channel, GPIO.RISING, callback=my_callback, bouncetime=200)

or

.. code:: python

   GPIO.add_event_callback(channel, my_callback, bouncetime=200)

Remove event detection
^^^^^^^^^^^^^^^^^^^^^^
If for some reason, your program no longer wishes to detect edge events, it is
possible to stop them:

.. code:: python

   GPIO.remove_event_detect(channel)


Outputs
-------
1. First set up OPi.GPIO

    .. code:: python

       import OPi.GPIO as GPIO
       GPIO.setmode(GPIO.BOARD)
       GPIO.setup(12, GPIO.OUT)

2. To set an output high:

    .. code:: python

       GPIO.output(12, GPIO.HIGH)
       # or
       GPIO.output(12, 1)
       # or
       GPIO.output(12, True)

3. To set an output low:

    .. code:: python

       GPIO.output(12, GPIO.LOW)
       # or
       GPIO.output(12, 0)
       # or
       GPIO.output(12, False)

4. To output to several channels at the same time:

    .. code:: python

       chan_list = (11,12)
       GPIO.output(chan_list, GPIO.LOW) # all LOW
       GPIO.output(chan_list, (GPIO.HIGH,GPIO.LOW))  # first LOW, second HIGH

5. Clean up at the end of your program

    .. code:: python

       GPIO.cleanup()

Note that you can read the current state of a channel set up as an output using
the :py:meth:`input()` function. For example to toggle an output:

    .. code:: python

       GPIO.output(12, not GPIO.input(12))


PWM
----
The PWM module is a hardware PWM feature, meaning that it uses the built in PWM chip
on the single board computer rather than any software timings or threads, this should
result in more accurate PWM signal that is less resorce taxing.

PWM is created in the form of an object.

1. First set up OPi.GPIO and create the object

    .. code:: python

       import OPi.GPIO as GPIO
       PWM_Class = GPIO.PWM(PWM_chip, PWM_pin, frequency_Hz, Duty_Cycle_Percent)

    Note currently you do not need to specify setmode before creating the class as for a GPIO
    only the PWM_chip number and the PWM_pin.
    The reson for this and how to find what they are is explained in the sysfs PWM section.

2. Begin the PWM cycle

    .. code:: python

        PWM_Class.start_pwm()

3. Change PWM duty Cycle

    .. code:: python
        PWM_Class.duty_cycle(50)

    Note this changes the Duty cycle to 50%

4. Change the frequency

    .. code:: python
        PWM_Class.change_frequency(500)

    Note this changes the Frequency to 500Hz

5. Stop the PWM device

    .. code:: python
        PWM_Class.stop_pwm()

    Note this stops the signal by setting the duty cycle to 0%

6. Change the Polarity of the signal

    .. code:: python
        PWM_Class.pwm_polarity()

    Note this changes swaps the on-off times. For example a duty cycle set to 75% before
    this will result in the signal being on 75% and off 25% of the time. After this is
    called it would be on 25% and off 75%.

7. Remove PWM Object

    .. code:: python
        PWM_Class.pwm_close()

SYSFS PWM:
----------
The PWM module uses the linux sysfs system to access and control the PWM chip on the single
board computer. More information can be found at:

https://developer.toradex.com/knowledge-base/pwm-linux

This code was written on an OrangePi PC+ so the following examples are based on that, however any single board
computer running linux that has a pwm chip will be able to use this.
To create a PWM object you write 0 to the file '/sys/class/pwm/pwmchip0/export'.
By writing 0 you are creating a pwm object called pwm0 that is tied to pwm pin 0.
This pin is RX pin of the DEBUG TTL UART pins (the middle pin of the pins between the power socket and HDMI).
The PWM commands are then controlled by writing into the files made at '/sys/class/pwm/pwmchip0/pwm0'.

Different single board computers may have pwm chip and pin names, currently the PWM pins have not been
mapped accross different boards, hence the need to specify the chip number and pin number at the start.
To find out what pins are available on your device you can follow the following steps:

1. Switch to Super User:

    .. code:: bash
        su root

2. List all pwm chips on the system:

    .. code:: bash
        ls -l /sys/class/pwm/

This will show all of the pwm chips on the system for example pwmchip0. The number following pwmchip is the
chip number used in PWM_chip. Some boards may have multiple chips, they will all be listed with that previous command.

3. Find the pin(s) associated with the chip:

    .. code:: bash
        echo 0 > /sys/class/pwm/pwmchip0/export

This writes '0' to the file 'export' which is under pwmchip0. If the chip has a pin 0 associated with it, an object that will
be created that can control the pwm pin. If a pin doesn't exisit an error will come up stating 'no such device'.
As of yet I do not know how to list out all of the available pins associated with a chip, there is a list at https://linux-sunxi.org/PIO
however not all pwm pins listed might be readily usable. For example on the OPi PC+ GPIO PA5 (physical pin 7) is listed as being PWM1 however it
is not accessable by default, likely it is reserved for something else and would probably require changing the DTC file before it can be accessed.

The best option would be to increase the number until you find a pin. You shouldn't need to go higher than 5 for any 1 chip.
The PWM pins dont follow the GPIO numbering system so the number are quite low.

4. List the created pwm pins:

    .. code:: bash
        ls /sys/class/pwm/pwmchip0

This lists all the files associated with pwmchip0. if you successfully created an object in step 3 you will see a pwm object (for example pwm0).
The number listed after pwm is the pin number used in PWM_pin.

LEDs:
-----
This code was written on an OrangePi PC+ so the following examples are based on that, however any single board
computer running linux that has a onboard leds be able to use this.

To list all LEDs on the system:

    .. code:: bash
        ls -l /sys/class/leds/

This will show all of the LEDs on the system for example orangepi:green:pwr.

1. To turn LED ON:

    .. code:: python

       GPIO.setled(GPIO.RED, GPIO.HIGH)
       # or
       GPIO.setled(GPIO.RED, 1)
       # or
       GPIO.setled(GPIO.RED, True)

2. To turn LED OFF:

    .. code:: python

       GPIO.setled(GPIO.RED, GPIO.LOW)
       # or
       GPIO.setled(GPIO.RED, 0)
       # or
       GPIO.setled(GPIO.RED, False)

3. To change several LEDs states at the same time:

    .. code:: python

       leds_list = [GPIO.RED, GPIO.GREEN]              # also works with tuples
       GPIO.led(leds_list, GPIO.HIGH)                  # sets both LEDs ON
       GPIO.led(leds_list, (GPIO.HIGH, GPIO.LOW))      # sets first LED ON and second LED OFF

Methods
-------
"""

import warnings

from OPi.constants import IN, OUT
from OPi.constants import LOW, HIGH                     # noqa: F401
from OPi.constants import NONE, RISING, FALLING, BOTH   # noqa: F401
from OPi.constants import BCM, BOARD, SUNXI, CUSTOM
from OPi.constants import PUD_UP, PUD_DOWN, PUD_OFF     # noqa: F401
from OPi.constants import RED, GREEN                    # LEDs
from OPi.pin_mappings import get_gpio_pin, set_custom_pin_mappings
from OPi import event, sysfs

_gpio_warnings = True
_mode = None
_exports = {}


def _check_configured(channel, direction=None):
    configured = _exports.get(channel)
    if configured is None:
        raise RuntimeError("Channel {0} is not configured".format(channel))

    if direction is not None and direction != configured:
        descr = "input" if configured == IN else "output"
        raise RuntimeError("Channel {0} is configured for {1}".format(channel, descr))


def getmode():
    """
    To detect which pin numbering system has been set.

    :returns: :py:attr:`GPIO.BOARD`, :py:attr:`GPIO.BCM`, :py:attr:`GPIO.SUNXI`
        or :py:attr:`None` if not set.
    """
    return _mode


def setmode(mode):
    """
    You must call this method prior to using all other calls.

    :param mode: the mode, one of :py:attr:`GPIO.BOARD`, :py:attr:`GPIO.BCM`,
        :py:attr:`GPIO.SUNXI`, or a `dict` or `object` representing a custom
        pin mapping.
    """
    if hasattr(mode, '__getitem__'):
        set_custom_pin_mappings(mode)
        mode = CUSTOM

    assert mode in [BCM, BOARD, SUNXI, CUSTOM]
    global _mode
    _mode = mode


def setwarnings(enabled):
    global _gpio_warnings
    _gpio_warnings = enabled


def setup(channel, direction, initial=None, pull_up_down=None):
    """
    You need to set up every channel you are using as an input or an output.

    :param channel: the channel based on the numbering system you have specified
        (:py:attr:`GPIO.BOARD`, :py:attr:`GPIO.BCM` or :py:attr:`GPIO.SUNXI`).
    :param direction: whether to treat the GPIO pin as input or output (use only
        :py:attr:`GPIO.IN` or :py:attr:`GPIO.OUT`).
    :param initial: (optional) When supplied and setting up an output pin,
        resets the pin to the value given (can be :py:attr:`0` / :py:attr:`GPIO.LOW` /
        :py:attr:`False` or :py:attr:`1` / :py:attr:`GPIO.HIGH` / :py:attr:`True`).
    :param pull_up_down: (optional) When supplied and setting up an input pin,
        configures the pin to 3.3V (pull-up) or 0V (pull-down) depending on the
        value given (can be :py:attr:`GPIO.PUD_OFF` / :py:attr:`GPIO.PUD_UP` /
        :py:attr:`GPIO.PUD_DOWN`)

    To configure a channel as an input:

    .. code:: python

       GPIO.setup(channel, GPIO.IN)

    To set up a channel as an output:

    .. code:: python

       GPIO.setup(channel, GPIO.OUT)

    You can also specify an initial value for your output channel:

    .. code:: python

       GPIO.setup(channel, GPIO.OUT, initial=GPIO.HIGH)

    **Setup more than one channel:**
    You can set up more than one channel per call. For example:

    .. code:: python

       chan_list = [11,12]    # add as many channels as you want!
                              # you can tuples instead i.e.:
                              #   chan_list = (11,12)
       GPIO.setup(chan_list, GPIO.OUT)
    """
    if _mode is None:
        raise RuntimeError("Mode has not been set")

    if pull_up_down is not None:
        if _gpio_warnings:
            warnings.warn("Pull up/down setting are not (yet) fully supported, continuing anyway. Use GPIO.setwarnings(False) to disable warnings.", stacklevel=2)

    if isinstance(channel, list):
        for ch in channel:
            setup(ch, direction, initial)
    else:
        if channel in _exports:
            raise RuntimeError("Channel {0} is already configured".format(channel))
        pin = get_gpio_pin(_mode, channel)
        try:
            sysfs.export(pin)
        except (OSError, IOError) as e:
            if e.errno == 16:   # Device or resource busy
                if _gpio_warnings:
                    warnings.warn("Channel {0} is already in use, continuing anyway. Use GPIO.setwarnings(False) to disable warnings.".format(channel), stacklevel=2)
                sysfs.unexport(pin)
                sysfs.export(pin)
            else:
                raise e

        sysfs.direction(pin, direction)
        _exports[channel] = direction
        if direction == OUT and initial is not None:
            sysfs.output(pin, initial)


def input(channel):
    """
    Read the value of a GPIO pin.

    :param channel: the channel based on the numbering system you have specified
        (:py:attr:`GPIO.BOARD`, :py:attr:`GPIO.BCM` or :py:attr:`GPIO.SUNXI`).
    :returns: This will return either :py:attr:`0` / :py:attr:`GPIO.LOW` /
        :py:attr:`False` or :py:attr:`1` / :py:attr:`GPIO.HIGH` / :py:attr:`True`).
    """
    _check_configured(channel)  # Can read from a pin configured for output
    pin = get_gpio_pin(_mode, channel)
    return sysfs.input(pin)


def output(channel, state):
    """
    Set the output state of a GPIO pin.

    :param channel: the channel based on the numbering system you have specified
        (:py:attr:`GPIO.BOARD`, :py:attr:`GPIO.BCM` or :py:attr:`GPIO.SUNXI`).
    :param state: can be :py:attr:`0` / :py:attr:`GPIO.LOW` / :py:attr:`False`
        or :py:attr:`1` / :py:attr:`GPIO.HIGH` / :py:attr:`True`.

    **Output to several channels:**
    You can output to many channels in the same call. For example:

    .. code:: python

       chan_list = [11,12]                             # also works with tuples
       GPIO.output(chan_list, GPIO.LOW)                # sets all to GPIO.LOW
       GPIO.output(chan_list, (GPIO.HIGH, GPIO.LOW))   # sets first HIGH and second LOW
    """
    if isinstance(channel, list):
        for ch in channel:
            output(ch, state)
    else:
        _check_configured(channel, direction=OUT)
        pin = get_gpio_pin(_mode, channel)
        return sysfs.output(pin, state)

def setled(led, state):
    """
    Set the state of a onboard LEDs.

    :param led: :py:attr:`GPIO.RED` or :py:attr:`GPIO.GREEN`.
    :param state: can be :py:attr:`0` / :py:attr:`GPIO.LOW` / :py:attr:`False`
        or :py:attr:`1` / :py:attr:`GPIO.HIGH` / :py:attr:`True`.

    **Several LEDs:**
    You can change state of both LEDs the same call. For example:

    .. code:: python

       leds_list = [GPIO.RED, GPIO.GREEN]              # also works with tuples
       GPIO.led(leds_list, GPIO.HIGH)                  # sets both LEDs ON
       GPIO.led(leds_list, (GPIO.HIGH, GPIO.LOW))      # sets first LED ON and second LED OFF
    """
    if isinstance(led, list):
        for l in led:
            setled(l, state)
    else:
        return sysfs.setled(led, state)

def wait_for_edge(channel, trigger, timeout=-1):
    """
    This function is designed to block execution of your program until an edge
    is detected.

    :param channel: the channel based on the numbering system you have specified
        (:py:attr:`GPIO.BOARD`, :py:attr:`GPIO.BCM` or :py:attr:`GPIO.SUNXI`).
    :param trigger: The event to detect, one of: :py:attr:`GPIO.RISING`,
        :py:attr:`GPIO.FALLING` or :py:attr:`GPIO.BOTH`.
    :param timeout: (optional) TODO

    In other words, the polling example above that waits for a button press
    could be rewritten as:

    .. code:: python

       GPIO.wait_for_edge(channel, GPIO.RISING)

    Note that you can detect edges of type :py:attr:`GPIO.RISING`,
    :py:attr`GPIO.FALLING` or :py:attr:`GPIO.BOTH`. The advantage of doing it
    this way is that it uses a negligible amount of CPU, so there is plenty left
    for other tasks.

    If you only want to wait for a certain length of time, you can use the
    timeout parameter:

    .. code:: python

       # wait for up to 5 seconds for a rising edge (timeout is in milliseconds)
       channel = GPIO.wait_for_edge(channel, GPIO_RISING, timeout=5000)
       if channel is None:
           print('Timeout occurred')
       else:
           print('Edge detected on channel', channel)
    """
    _check_configured(channel, direction=IN)
    pin = get_gpio_pin(_mode, channel)
    if event.blocking_wait_for_edge(pin, trigger, timeout) is not None:
        return channel


def add_event_detect(channel, trigger, callback=None, bouncetime=None):
    """
    This function is designed to be used in a loop with other things, but unlike
    polling it is not going to miss the change in state of an input while the
    CPU is busy working on other things. This could be useful when using
    something like Pygame or PyQt where there is a main loop listening and
    responding to GUI events in a timely basis.

    :param channel: the channel based on the numbering system you have specified
        (:py:attr:`GPIO.BOARD`, :py:attr:`GPIO.BCM` or :py:attr:`GPIO.SUNXI`).
    :param trigger: The event to detect, one of: :py:attr:`GPIO.RISING`,
        :py:attr:`GPIO.FALLING` or :py:attr:`GPIO.BOTH`.
    :param callback: (optional) TODO
    :param bouncetime: (optional) TODO

    .. code: python

       GPIO.add_event_detect(channel, GPIO.RISING)  # add rising edge detection on a channel
       do_something()
       if GPIO.event_detected(channel):
           print('Button pressed')
    """
    _check_configured(channel, direction=IN)

    if bouncetime is not None:
        if _gpio_warnings:
            warnings.warn("bouncetime is not (yet) fully supported, continuing anyway. Use GPIO.setwarnings(False) to disable warnings.", stacklevel=2)

    pin = get_gpio_pin(_mode, channel)
    event.add_edge_detect(pin, trigger, __wrap(callback, channel))


def remove_event_detect(channel):
    """
    :param channel: the channel based on the numbering system you have specified
        (:py:attr:`GPIO.BOARD`, :py:attr:`GPIO.BCM` or :py:attr:`GPIO.SUNXI`).
    """
    _check_configured(channel, direction=IN)
    pin = get_gpio_pin(_mode, channel)
    event.remove_edge_detect(pin)


def add_event_callback(channel, callback, bouncetime=None):
    """
    :param channel: the channel based on the numbering system you have specified
        (:py:attr:`GPIO.BOARD`, :py:attr:`GPIO.BCM` or :py:attr:`GPIO.SUNXI`).
    :param callback: TODO
    :param bouncetime: (optional) TODO
    """
    _check_configured(channel, direction=IN)

    if bouncetime is not None:
        if _gpio_warnings:
            warnings.warn("bouncetime is not (yet) fully supported, continuing anyway. Use GPIO.setwarnings(False) to disable warnings.", stacklevel=2)

    pin = get_gpio_pin(_mode, channel)
    event.add_edge_callback(pin, __wrap(callback, channel))


def event_detected(channel):
    """
    This function is designed to be used in a loop with other things, but unlike
    polling it is not going to miss the change in state of an input while the
    CPU is busy working on other things. This could be useful when using
    something like Pygame or PyQt where there is a main loop listening and
    responding to GUI events in a timely basis.

    .. code:: python

       GPIO.add_event_detect(channel, GPIO.RISING)  # add rising edge detection on a channel
       do_something()
       if GPIO.event_detected(channel):
           print('Button pressed')

    Note that you can detect events for :py:attr:`GPIO.RISING`,
    :py:attr:`GPIO.FALLING` or :py:attr:`GPIO.BOTH`.

    :param channel: the channel based on the numbering system you have specified
        (:py:attr:`GPIO.BOARD`, :py:attr:`GPIO.BCM` or :py:attr:`GPIO.SUNXI`).
    :returns: :py:attr:`True` if an edge event was detected, else :py:attr:`False`.
    """
    _check_configured(channel, direction=IN)
    pin = get_gpio_pin(_mode, channel)
    return event.edge_detected(pin)


def __wrap(callback, channel):
    if callback is not None:
        return lambda _: callback(channel)


def cleanup(channel=None):
    """
    At the end any program, it is good practice to clean up any resources you
    might have used. This is no different with OPi.GPIO. By returning all
    channels you have used back to inputs with no pull up/down, you can avoid
    accidental damage to your Orange Pi by shorting out the pins. Note that
    this will only clean up GPIO channels that your script has used. Note that
    GPIO.cleanup() also clears the pin numbering system in use.

    To clean up at the end of your script:

    .. code:: python

       GPIO.cleanup()

    It is possible that don't want to clean up every channel leaving some set
    up when your program exits. You can clean up individual channels, a list or
    a tuple of channels:

    .. code:: python

       GPIO.cleanup(channel)
       GPIO.cleanup( (channel1, channel2) )
       GPIO.cleanup( [channel1, channel2] )
    """
    if channel is None:
        cleanup(list(_exports.keys()))
        setwarnings(True)
        global _mode
        _mode = None
    elif isinstance(channel, list):
        for ch in channel:
            cleanup(ch)
    else:
        _check_configured(channel)
        pin = get_gpio_pin(_mode, channel)
        event.cleanup(pin)
        sysfs.unexport(pin)
        del _exports[channel]


class PWM:

    # To Do:
    # 1. Start tracking pwm cases to  list like _exports say _exports_pwm
    # 2. find way to check _exports against _exports_pwm to make sure there is no overlap.
    # 3. Create map of pwm pins to various boards.

    def __init__(self, chip, pin, frequency, duty_cycle_percent, invert_polarity=False):  # (pwm pin, frequency in KHz)

        """
        Setup the PWM object to control.

        :param chip: the pwm chip number you wish to use.
        :param pin: the pwm pin number you wish to use.
        :param frequency: the frequency of the pwm signal in hertz.
        :param duty_cycle_percent: the duty cycle percentage.
        :param invert_polarity: invert the duty cycle.
            (:py:attr:`True` or :py:attr:`False`).
        """

        self.chip = chip
        self.pin = pin
        self.frequency = frequency
        self.duty_cycle_percent = duty_cycle_percent
        self.invert_polarity = invert_polarity

        try:
            sysfs.PWM_Export(chip, pin)  # creates the pwm sysfs object
            if invert_polarity is True:
                sysfs.PWM_Polarity(chip, pin, invert=True)  # invert pwm i.e the duty cycle tells you how long the cycle is off
            else:
                sysfs.PWM_Polarity(chip, pin, invert=False)  # don't invert the pwm signal. This is the normal way its used.
            sysfs.PWM_Enable(chip, pin)
            return sysfs.PWM_Frequency(chip, pin, frequency)

        except (OSError, IOError) as e:
            if e.errno == 16:   # Device or resource busy
                warnings.warn("Pin {0} is already in use, continuing anyway.".format(pin), stacklevel=2)
                sysfs.PWM_Unexport(chip, pin)
                sysfs.PWM_Export(chip, pin)
            else:
                raise e

    def start_pwm(self):  # turn on pwm by setting the duty cycle to what the user specified
        """
        Start PWM Signal.
        """
        return sysfs.PWM_Duty_Cycle_Percent(self.chip, self.pin, self.duty_cycle_percent)  # duty cycle controls the on-off

    def stop_pwm(self):  # turn on pwm by setting the duty cycle to 0
        """
        Stop PWM Signal.
        """
        return sysfs.PWM_Duty_Cycle_Percent(self.chip, self.pin, 0)  # duty cycle at 0 is the equivilant of off

    def change_frequency(self, new_frequency):
        # Order of opperations:
        # 1. convert to period
        # 2. check if period is increasing or decreasing
        # 3. If increasing update pwm period and then update the duty cycle period
        # 4. If decreasing update the duty cycle period and then the pwm period
        # Why:
        # The sysfs rule for PWM is that PWM Period >= duty cycle period (in nanosecs)

        """
        Change the frequency of the signal.

        :param new_frequency: the new PWM frequency.
        """

        pwm_period = (1 / new_frequency) * 1e9
        pwm_period = int(round(pwm_period, 0))
        duty_cycle = (self.duty_cycle_percent / 100) * pwm_period
        duty_cycle = int(round(duty_cycle, 0))

        old_pwm_period = int(round((1 / self.frequency) * 1e9, 0))

        if (pwm_period > old_pwm_period):  # if increasing
            sysfs.PWM_Period(self.chip, self.pin, pwm_period)  # update the pwm period
            sysfs.PWM_Duty_Cycle(self.chip, self.pin, duty_cycle)  # update duty cycle

        else:
            sysfs.PWM_Duty_Cycle(self.chip, self.pin, duty_cycle)  # update duty cycle
            sysfs.PWM_Period(self.chip, self.pin, pwm_period)  # update pwm freq

        self.frequency = new_frequency  # update the frequency

    def duty_cycle(self, duty_cycle_percent):  # in percentage (0-100)
        """
        Change the duty cycle of the signal.

        :param duty_cycle_percent: the new PWM duty cycle as a percentage.
        """

        if (0 <= duty_cycle_percent <= 100):
            self.duty_cycle_percent = duty_cycle_percent
            return sysfs.PWM_Duty_Cycle_Percent(self.chip, self.pin, self.duty_cycle_percent)
        else:
            raise Exception("Duty cycle must br between 0 and 100. Current value: {0} is out of bounds".format(duty_cycle_percent))

    def pwm_polarity(self):  # invert the polarity of the pwm
        """
        Invert the signal.
        """
        sysfs.PWM_Disable(self.chip, self.pin)
        sysfs.PWM_Polarity(self.chip, self.pin, invert=not(self.invert_polarity))
        sysfs.PWM_Enable(self.chip, self.pin)

    def pwm_close(self):
        """
        remove the object from the system.
        """
        sysfs.PWM_Unexport(self.chip, self.pin)
