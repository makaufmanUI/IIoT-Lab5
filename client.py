"""
client.py
=========

A simple echo client that sends messages to the server
for the purpose of sending commands to the RPi to control the stepper motor.
"""
import os
import sys
import socket




class Client:
    def __init__(self,serverIP,serverPort):
        self.serverIP = serverIP
        self.serverPort = serverPort
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    
    def connect_to_server(self) -> None:
        self.socket.connect((self.serverIP,self.serverPort))
        print(f"\n\n>> Connected to {self.serverIP}:{self.serverPort}.\n\n")
    
    def send(self,message) -> None:
        self.socket.send(str.encode(message))
        print(f"\n      >>     Sent: \"{message}\"")
    
    def receive(self,bufferSize) -> None:
        message = self.socket.recv(bufferSize)
        if message:
            print(f"      >> Received: \"{message.decode('utf-8')}\"\n\n")

    def close_connection(self) -> None:
        self.socket.close()
        print(">> Connection closed.\n\n\n")







if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n\nValid commands:")
    print(    "---------------\n")
    print(    "   >  \"q\":  quit the program")
    print(    "   -  \"c\":  close the connection")
    print(    "   -  \"h\":  return the stepper motor to home position")
    print(    "   -  \"sh\": set current position to new home position")
    print(    "   -  \"rh\": reset the home position to the default home position")
    print(    "   -  \"direction, angle, speed\":  move the stepper motor as specified\n\n")
    
    TCP_PORT = 5005
    BUFFER_SIZE = 1024
    TCP_IP = '192.168.1.13'
    
    client = Client(TCP_IP,TCP_PORT)
    client.connect_to_server()
    
    while True:
        userInput = input("   >> Input command:  ")
        
        if userInput == "q":
            break
        elif userInput == "c":
            client.send(userInput)
            client.receive(BUFFER_SIZE)
            client.close_connection()
            break
        else:
            client.send(userInput)
            client.receive(BUFFER_SIZE)
    
    sys.exit()