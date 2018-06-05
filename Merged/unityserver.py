from naoqi import ALProxy
import vision_definitions
import almath
import socket
import time

# Python to NAO Robot socket
class PythonToNao:
    IP = "192.168.137.18"
    PORT = 9559
    FRAME_TORSO = 0
    USE_SENSOR = False
    ARM_LENGTH = .21

    def __init__(self):
        # Wake up Nao motors
        self.motion = ALProxy("ALMotion", PythonToNao.IP, PythonToNao.PORT)
        self.motion.wakeUp()
        
        # Set Nao to start pose and get initial positions
        posture = ALProxy("ALRobotPosture", PythonToNao.IP, PythonToNao.PORT)
        posture.goToPosture("Stand", .5)
        self.LArmInit = self.motion.getPosition("LArm", PythonToNao.FRAME_TORSO, PythonToNao.USE_SENSOR)
        self.RArmInit = self.motion.getPosition("RArm", PythonToNao.FRAME_TORSO, PythonToNao.USE_SENSOR)

        # Speech and Camera
        self.tts = ALProxy("ALTextToSpeech", PythonToNao.IP, PythonToNao.PORT)
        self.camera = ALProxy("ALVideoDevice", PythonToNao.IP, PythonToNao.PORT)
        self.handle = self.camera.subscribeCamera("MyModule", 2, vision_definitions.kVGA, vision_definitions.kRGBColorSpace, 30)

    def getMotionProxy(self):
        return self.motion
    
    def getTextToSpeechProxy(self):
        return self.tts

    def getVideoDeviceProxy(self):
        return self.camera
    
    def close(self):
        self.motion.rest()
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

        self.conn.setblocking(0) # don't block on calls to recv
    
    def recv(self, buffersize):
        try:
            return self.conn.recv(buffersize) if hasattr(self, 'conn') else None
        except socket.error:
            return None

    def send(self, message):
        if hasattr(self, 'conn'):
            try:
                self.conn.send(message) 
            except socket.error as e:
                print e # Do not crash script
    
    def close(self):
        if hasattr(self, 'conn'):
            self.conn.close() 

# Returns true if DISCONNECT, false otherwise
def processCommands(commands, naoConnection):
    FRAME_TORSO = 0
    POSITION_ONLY = 7

    # parse all commands from received string (newline separated)
    parsedCommands = commands.splitlines()
    for command in parsedCommands:
        if command == "DISCONNECT":
            return True
        else:
            command = command.split("|")
            if command[0] == "MOVE":
                if len(command) == 3:
                    if naoConnection:
                        # Moving arms: sent position vector is from user shoulder to user hand.
                        if command[1].find("Arm") != -1:
                            # Get position array
                            handPosition = command[2][1:-1].replace(" ", "")
                            handPosition = handPosition.split(",") 

                            # turn into float array and convert Unity coordinates to NAO coordinates
                            armInit = []
                            if command[1] == "LArm":
                                armInit = naoConnection.LArmInit
                            else:
                                armInit = naoConnection.RArmInit

                            handPosition = [armInit[0] + float(handPosition[2]) * PythonToNao.ARM_LENGTH,    # z = x
                                    armInit[1] + -float(handPosition[0]) * PythonToNao.ARM_LENGTH,           #-x = y
                                    armInit[2] + float(handPosition[1]) * PythonToNao.ARM_LENGTH]            # y = z

                            # Plus wx, wy, wz (rotation)
                            handPosition = handPosition + [0.0, 0.0, 0.0]

                            # Move arm
                            naoConnection.getTextToSpeechProxy().say("MOVE")
                            naoConnection.getMotionProxy().setPosition(command[1], FRAME_TORSO, handPosition, 1, POSITION_ONLY)
            if command[0] == "SAY":
                if len(command) == 2:
                    print command[0] + ":", command[1]
                    if naoConnection:
                        naoConnection.getTextToSpeechProxy().say(command[1])
    return False

def sendUpdates(unityConnection, naoConnection):
    # Send left arm position
    # LArmPos = convertNaoPosToStr(naoConnection.getMotionProxy().getPosition("LArm", 0, False))
    # unityConnection.send("LARM|" + LArmPos)

    # Test if whole array can be sent in one packet
    videoProxy = naoConnection.getVideoDeviceProxy()
    image = videoProxy.getImageRemote(naoConnection.handle)
    unityConnection.send("IMG|" + image[6])
    videoProxy.releaseImage(naoConnection.handle)
    

# Takes position from ALMotionProxy.getPosition() and converts into list without spaces or square brackets
# x,y,z,wx,wy,wz (in radians)
def convertNaoPosToStr(LArmPos):
    LArmString = str(LArmPos[0])
    for i in range(1, len(LArmPos)):
        LArmString += "," + str(LArmPos[i])
    return LArmString

# ----------------MAIN CODE--------------------

# Communicate with Nao
print "Starting nao connection"
naoConnection = PythonToNao()
processCommands("SAY|Connected to Nao", naoConnection)
time.sleep(1)

# Communicate with Unity
print "Starting unity connection"
unityConnection = PythonToUnity()
unityConnection.connect()

# Main Loop
while 1:
    # Receive data from unity
    newdata = unityConnection.recv(1024)

    # null means connection was severed (according to python, doesn't seem true for now)
    # or that Unity didn't send anything (only sends about once per second)
    if newdata:
        # Receive commands from Unity
        if processCommands(newdata, naoConnection):
            # Handle received disconnect command here
            print "Received Disconnect"
            break
    
    # Send commands to Unity
    sendUpdates(unityConnection, naoConnection)

    # wait one second between calls to recv to not overflow NAO robot
    # time.sleep(1)

# Exit
print "Closing connection"
unityConnection.close()
naoConnection.close()