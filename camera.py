import time
import vision_definitions
from naoqi import ALProxy
import png

IP = "192.168.137.18"
PORT = 9559

camera = ALProxy("ALVideoDevice", IP, PORT)
handle = camera.subscribeCamera("MyModule", 2, 
    vision_definitions.kVGA, vision_definitions.kRGBColorSpace, 30)

image = camera.getImageRemote(handle)

print image[0], image[1], image[3], len(image[6])
with open("nao_pic1.txt", "wb") as file:
    for byte in image[6]:
        file.write(str(ord(byte)) + " ")

camera.releaseImage(handle)

camera.unsubscribe(handle)