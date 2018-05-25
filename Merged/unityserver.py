from naoqi import ALProxy
import vision_definitions
import almath
import socket
import time

# Python to NAO Robot socket
class PythonToNao:
    IP = "192.168.137.18"
    PORT = 9559

    def __init__(self):
        self.tts = ALProxy("ALTextToSpeech", PythonToNao.IP, PythonToNao.PORT)
        self.motion = ALProxy("ALMotion", PythonToNao.IP, PythonToNao.PORT)
        self.camera = ALProxy("ALVideoDevice", PythonToNao.IP, PythonToNao.PORT)
        self.camera.unsubscribe("MyModule")
        self.handle = self.camera.subscribeCamera("MyModule", 2, 
            vision_definitions.kVGA, vision_definitions.kRGBColorSpace, 30)

    def getMotionProxy(self):
        return self.motion
    
    def getTextToSpeechProxy(self):
        return self.tts

    def getVideoDeviceProxy(self):
        return self.camera
    
    def close(self):
        self.camera.unsubscribe(self.handle)

# Python to Unity socket
class PythonToUnity:
    IP = "localhost"
    PORT_NUM = 10000
    
    # Connects to NAO robot
    def __init__(self):
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.bind((PythonToUnity.IP, PythonToUnity.PORT_NUM))
        self.serversocket.listen(1)

    def connect(self):
        # Wait for client to connect to server
        print "Connecting to localhost:", self.PORT_NUM
        self.conn, self.addr = self.serversocket.accept()
        print "Connected to", self.addr
        print "To close the server, close the client (to send a DISCONNECT signal)."
    
    def recv(self, buffersize):
        return self.conn.recv(buffersize) if hasattr(self, 'conn') else None

    def send(self, message):
        if hasattr(self, 'conn'):
            self.conn.send(message) 
    
    def close(self):
        if hasattr(self, '_conn'):
            self.conn.close() 

# Returns true if DISCONNECT, false otherwise
def processCommands(commands, naoConnection):
    # parse all commands from received string (newline separated)
    parsedCommands = commands.splitlines()
    for command in parsedCommands:
        if command == "DISCONNECT":
            return True
        else:
            command = command.split("|")
            if command[0] == "MOVE":
                if len(command) == 3:
                    position = command[2][1:-1].replace(" ", "")
                    print command[0], command[1], "to", position
                    if naoConnection:
                        naoConnection.getTextToSpeechProxy().say("MOVE")

                    # FIXME: Finish this
                    #FRAME_TORSO = 0
                    #POSITION_ONLY = 7
                    #position = None # convert command[2] to float array?
                    #naoConnection.getMotionProxy().setPosition(command[1], FRAME_TORSO, position, .2, POSITION_ONLY)
            if command[0] == "SAY":
                if len(command) == 2:
                    print command[0] + ":", command[1]
                    if naoConnection:
                        naoConnection.getTextToSpeechProxy().say(command[1])
    return False

def sendUpdates(unityConnection, naoConnection):
    # Send left arm position
    LArmPos = convertNaoPosToStr(naoConnection.getMotionProxy().getPosition("LArm", 0, False))
    unityConnection.send("LARM|" + LArmPos)

# Takes position from ALMotionProxy.getPosition() and converts into list without spaces or square brackets
# x,y,z,wx,wy,wz (in radians)
def convertNaoPosToStr(LArmPos):
    LArmString = str(LArmPos[0])
    for i in range(1, len(LArmPos)):
        LArmString += "," + str(LArmPos[i])
    return LArmString

# ----------------MAIN CODE--------------------

# Communicate with Unity
print "Starting unity connection"
unityConnection = PythonToUnity()
unityConnection.connect()

# Communicate with Nao
print "Starting nao connection"
naoConnection = PythonToNao()
processCommands("SAY|Connected to Nao", naoConnection)
time.sleep(1)
#naoConnection = None

# Main Loop
while 1:
    # # Receive data from unity
    # newdata = unityConnection.recv(1024)

    # # null means connection was severed? According to python. Doesn't seem true for now.
    # if not newdata:
    #     # break
    #     continue
    
    # # Receive commands from Unity
    # if processCommands(newdata, naoConnection):
    #     # Handle received disconnect command here
    #     print "Received Disconnect"
    #     break
    
    # Send commands to Unity
    sendUpdates(unityConnection, naoConnection)

    # wait one second between calls to recv to not overflow NAO robot
    time.sleep(.1)

# Exit
print "Closing connection"
unityConnection.close()
naoConnection.close()