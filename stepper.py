"""
stepper.py
==========

Defines the Stepper class,
which exposes several methods for controlling the stepper motor.
"""
from math import floor
import RPi.GPIO as GPIO
from functions import sleep, normalize, to_angle

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)





class Stepper:
    def __init__(self,enablePin,coilA1Pin,coilA2Pin,coilB1Pin,coilB2Pin):
        # set initial values
        self.delay = 0.00195            # delay between steps (this delay corresponds to maximum speed)
        self.stepsFromHome = 0          # keeps track of steps away from home (+cw, -ccw); i.e. if pos., must rotate cw to go home
        self.stepsFromDefaultHome = 0   # keeps track of steps away from default home, even if user sets a new home
        # set speed limits
        self.minSpeed = 10          # 10s / rotation, minimium speed
        self.maxSpeed =  4          #  4s / rotation, maximum speed
        # initialize pins
        self.enablePin = enablePin
        self.coilA1Pin = coilA1Pin
        self.coilA2Pin = coilA2Pin
        self.coilB1Pin = coilB1Pin
        self.coilB2Pin = coilB2Pin
        # set pin modes
        GPIO.setup(self.enablePin, GPIO.OUT)
        GPIO.setup(self.coilA1Pin, GPIO.OUT)
        GPIO.setup(self.coilA2Pin, GPIO.OUT)
        GPIO.setup(self.coilB1Pin, GPIO.OUT)
        GPIO.setup(self.coilB2Pin, GPIO.OUT)
        # set enable pin to high
        GPIO.output(self.enablePin,1)
        
    
    
    def set_LEDs(self,red,blue,green,orange):
        """
        Gives the stepper object access to the LEDs.
        Allows the motor to control their state when operating.
        """
        self.redLED = red
        self.blueLED = blue
        self.greenLED = green
        self.orangeLED = orange
        self.redLED.on()
    
    
    
    def set_delay(self,delay):
        """
        Sets the delay between steps that
        the stepper motor will use when rotating.
        Never used directly, but used by set_speed() and set_speed_pct().
        """
        self.delay = delay
    
    
    
    def set_speed(self,secPerRev):
        """
        Sets the speed of the stepper motor in absolute terms.
        Never used directly, but used by set_speed_pct().
        Using this method as an intermediate step allows for easier exception handling.
        """
        if secPerRev < self.maxSpeed:
            raise ValueError("The stepper cannot complete a revolution in under 4 seconds.")
        self.delay = secPerRev/2050
    
    
    
    def set_speed_pct(self,pct):
        """
        Sets the speed of the stepper motor as a percentage of maximum speed.
        The given percentage can be expressed as a normal percentage or decimal percentage.
        """
        if pct <=  1: pct *= 100    # if given as decimal, convert to normal
        if pct > 100: pct = 100     # adjust any values above 100 to 100
        if pct <   0: pct = 0       # adjust any values below 0 to 0
        self.set_speed( self.minSpeed - (pct/100)*(self.minSpeed-self.maxSpeed) )
    
    
    
    def set_step(self,A1,A2,B1,B2):
        """
        Sets the stepper motor to the given step.
        Never used directly, but used by rotate() and deactivate().
        """
        GPIO.output(self.coilA1Pin,A1)
        GPIO.output(self.coilA2Pin,A2)
        GPIO.output(self.coilB1Pin,B1)
        GPIO.output(self.coilB2Pin,B2)
        
        
        
    def deactivate(self):
        """
        Deactivates the stepper motor
        and removes any holding torque.
        """
        self.set_step(0,0,0,0)
        self.redLED.on()
        self.blueLED.off()
        self.greenLED.off()
        self.orangeLED.off()
    
    
    
    def num_steps_required(self,angle):
        """
        Returns the number of steps required
        to rotate the stepper motor to the given angle (lowball).
        """
        return int(round(1.4222*angle,0))
    
    

    def rotate(self,direction,angle=None,steps=None):
        """
        Rotates the stepper motor in the specified direction.
        The direction can be specified as either 'cw' or 'ccw'.
        The angle or number of steps can be specified to dictate rotation,
        as homing requires a specific number of steps to return to home accurately.
        """
        # ensure the specified direction is valid
        if direction.lower() not in ['cw','ccw']:
            print("   >>   [Stepper] Invalid direction: {}".format(direction))
            return
        
        # set the number of steps to rotate, regardless of whether angle or steps was given
        numSteps = self.num_steps_required(angle) if angle else steps if steps else None
        
        if not numSteps:    # exit method if angle nor steps was given
            print("   >>   [Stepper] No angle or steps specified.")
            return
        if not angle:       # if steps was given, calculate the approximate angle
            angle = f"~{to_angle(numSteps)}"


        self.redLED.off()
        if direction.lower() == 'cw':
            self.blueLED.on()
            self.greenLED.on()
            # update stepsFromHome
            self.stepsFromHome -= numSteps
            self.stepsFromDefaultHome -= numSteps
            print("      [Stepper] Rotating {} degrees CW ({} steps).\n\n".format(angle,numSteps))
            # rotate clockwise
            for i in range(numSteps):
                self.set_step(1,0,0,1)
                sleep(self.delay)
                self.set_step(0,1,0,1)
                sleep(self.delay)
                self.set_step(0,1,1,0)
                sleep(self.delay)
                self.set_step(1,0,1,0)
                sleep(self.delay)
        
        elif direction.lower() == 'ccw':
            self.greenLED.on()
            self.orangeLED.on()
            # update stepsFromHome
            self.stepsFromHome += numSteps
            self.stepsFromDefaultHome += numSteps
            print("      [Stepper] Rotating {} degrees CCW ({} steps).\n\n".format(angle,numSteps))
            # rotate counter-clockwise
            for i in range(numSteps):
                self.set_step(1,0,1,0)
                sleep(self.delay)
                self.set_step(0,1,1,0)
                sleep(self.delay)
                self.set_step(0,1,0,1)
                sleep(self.delay)
                self.set_step(1,0,0,1)
                sleep(self.delay)
        
        self.deactivate()   # deactivate the stepper motor when done rotating

    
    
    def go_home(self,default=True):
        """
        Rotates the stepper motor to the home position.
        The default home position (where it was on program start) is assumed to be the target home position.
        If default is set to False, the stepper will go to the user-defined home position instead.
        """
        if default: stepsFromHome = self.stepsFromDefaultHome
        else:       stepsFromHome = self.stepsFromHome
        
        # print the steps required to go home, and in what direction
        if stepsFromHome > 0:
            print("      [Stepper] Going Home: {} steps CW from here (~{} degrees).".format(stepsFromHome, to_angle(stepsFromHome)))
        else:
            print("      [Stepper] Going Home: {} steps CCW from here (~{} degrees).".format(abs(stepsFromHome), to_angle(stepsFromHome)))
        
        # normalize the steps required to go home
        steps = normalize(stepsFromHome,-256,256)
        
        # if already at home, exit method
        if steps == 0:
            print("      [Stepper] Already home.")
            return
        
        if steps < 0:
              self.rotate('ccw',steps=abs(steps))   # rotate CCW if stepsFromHome is negative
        else: self.rotate('cw',steps=steps)         # rotate CW if stepsFromHome is positive
        
        # display the new stepsFromHome and reset it
        # print("      [Stepper] Steps from home: {} (~{} degrees)\n\n".format(
        #     normalize(stepsFromHome,-256,256),normalize(to_angle(stepsFromHome),-180,180)
        # ))
        if default: self.stepsFromDefaultHome = 0
        else:       self.stepsFromHome = 0
        self.stepsFromHome = 0
    


    def set_home(self):
        """
        Sets the current position as the home position.
        """
        self.stepsFromHome = 0
        print("      [Stepper] New home set.\n\n")
    


    def reset_home(self):
        """
        Resets the home position to the default home position.
        """
        self.stepsFromHome = self.stepsFromDefaultHome
        print("      [Stepper] Home reset.\n\n")