import png

imageFile = open("nao_pic1.txt", "r")
imageContents = imageFile.read()
print len(imageContents)

# 320 by 240
rgbArray = []
for j in range(0, 1187):
    rgbRow = []
    rowIdx = j*14*3
    for i in range(0, 14):
        colIdx = i*3
        print rowIdx, colIdx, j, i
        rgbRow += [ord(imageContents[rowIdx + colIdx]), 
            ord(imageContents[rowIdx + colIdx + 1]), 
            ord(imageContents[rowIdx + colIdx + 2])]
    rgbArray.append(tuple(rgbRow))

imageRGB = open("nao_pic1.png", "wb")
w = png.Writer(14, 1187)
w.write(imageRGB, rgbArray)

imageFile.close()
imageRGB.close()