from PIL import Image, ImageChops
import aircv


imgsource = aircv.imread(r"F:\J01.PNG")
imgsearch = aircv.imread(r"F:\radio.bmp")
imgdiff = aircv.find_all_template(imgsource, imgsearch, threshold=0.9)

print(imgdiff)
