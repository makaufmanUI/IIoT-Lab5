"""
server.py
=========

A simple echo server that receives messages from a client
for the purpose of interpreting commands and relaying them to the stepper motor.
"""
import os
import sys
import socket
from led import LED
from stepper import Stepper
from functions import get_ip, parse





class Server:
    def __init__(self,ip,tcpPort):
        self.ip = ip
        self.port = tcpPort
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.clientAddress = None
        self.socket.bind((self.ip,self.port))
        
    def wait_for_connection(self) -> None:
        self.socket.listen(1)
        print(f"\n\n>> Listening on {self.ip}:{self.port} ... ", end="")
    
    def accept_connection(self) -> None:
        self.connection,clientAddress = self.socket.accept()
        if self.clientAddress is None:
            print("connection with {}:{} opened.\n\n".format(*clientAddress))
        elif clientAddress[0] != self.clientAddress[0]:
            print("connection with {}:{} opened.\n\n".format(*clientAddress))
        self.clientAddress = clientAddress
    
    def receive_data(self,bufferSize) -> str:
        self.data = self.connection.recv(bufferSize)
        if not self.data: return None
        print(f"   >> Received: \"{self.data.decode('utf-8')}\"")
        return self.data.decode("utf-8")
    
    def send(self,message) -> None:
        if isinstance(message,list):
            message = ",".join([str(item) for item in message])
        self.message = str.encode(message)
        self.connection.sendall(message.encode("utf-8"))
        print(f"   >>     Sent: \"{message}\"\n\n")
    
    def close_connection(self) -> None:
        self.send("Closing connection.")
        self.connection.close()
        print(">> Connection with {}:{} closed.\n\n\n".format(*self.clientAddress))







if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # initialize LEDs and stepper motor
    red = LED(22)
    blue = LED( 5)
    green = LED(27)
    orange = LED( 6)
    stepper = Stepper(26, 4, 17, 23, 24)
    stepper.set_LEDs(red,blue,green,orange)


    # get IP and initialize server
    IP = get_ip()
    server = Server(IP,5005)
    server.wait_for_connection()
    isHomeDefault = True        # flag to indicate whether home position is default or user-defined
    
    
    while True:
        server.accept_connection()
        
        while True:
            data = server.receive_data(1024)
            if not data:
                break
            
            if data.lower() == "c":
                server.close_connection()
                sys.exit()
            
            if ',' in data:
                commands = parse(data)      # parse the message/data into a list of commands
                if commands:
                    direction,angle,speed = commands
                    server.send("Sending command to stepper.")
                    stepper.set_speed_pct(speed)
                    stepper.rotate(direction,angle)
                else:
                    server.send("TypeError in command.")
                
            elif data.lower() == "h":
                server.send("Sending stepper to home position.")
                stepper.go_home(isHomeDefault)      # go to home position, either default or user-defined based on flag
            
            elif data.lower() == "sh":
                server.send("Setting current position to new home.")
                stepper.set_home()
                isHomeDefault = False               # set flag to indicate that home position is user-defined
            
            elif data.lower() == "rh":
                server.send("Resetting home position to default.")
                stepper.reset_home()
                isHomeDefault = True                # set flag to indicate that home position is default
            
            else:
                server.send("Invalid command.")