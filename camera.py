import time
import vision_definitions
from naoqi import ALProxy
import png

IP = "192.168.137.18"
PORT = 9559

camera = ALProxy("ALVideoDevice", IP, PORT)
handle = camera.subscribeCamera("MyModule", 2, 
    vision_definitions.kQVGA, vision_definitions.kRGBColorSpace, 30)

image = camera.getImageRemote(handle)

print image[0], image[1]
for i in range(0,10):
    print ord(image[6][i])
# with open("nao_pic1.txt", "w") as file:
#     file.write(image[6])

camera.releaseImage(handle)

camera.unsubscribe(handle)