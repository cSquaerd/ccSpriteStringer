import sys
import cv2 as cv
import numpy as np
import colorama as cr
# Compute (crudely) which basic color each pixel is closest to in RGB space,
# and return a paletted image along with some other metrics
def convertTo16Color(image : np.array, darkDelta : int = 0x55) -> dict:
	f = 0xff # Full
	h = 0x55 # Half
	# Define gray-shades & colors
	black = np.array([0, 0, 0], np.int16)
	white = np.array([f, f, f], np.int16)
	
	darkGray = np.minimum(white - darkDelta, black + darkDelta)
	lightGray = np.maximum(white - darkDelta, black + darkDelta)
	
	red = np.array([h, h, f], np.int16)
	redDim = np.maximum(red - darkDelta, 0)
	
	green = np.array([h, f, h], np.int16)
	greenDim = np.maximum(green - darkDelta, 0)
	
	blue = np.array([f, h, h], np.int16)
	blueDim = np.maximum(blue - darkDelta, 0)
	
	magenta = np.array([f, h, f], np.int16)
	magentaDim = np.maximum(magenta - darkDelta, 0)
	
	yellow = np.array([h, f, f], np.int16)
	yellowDim = np.maximum(yellow - darkDelta, 0)
	
	cyan = np.array([f, f, h], np.int16)
	cyanDim = np.maximum(cyan - darkDelta, 0)
	# Check if the image has an alpha channel, and separate it if so
	transparent = False
	if image.shape[2] > 3:
		transparent = True
		whereTransparent = image[:, :, 3] == 0
		image = image[:, :, :3]
	# Line up the color values we will be using
	colors = np.stack(
		[
			redDim, greenDim, blueDim, yellowDim, magentaDim, cyanDim,
			red, green, blue, yellow, magenta, cyan
		]
	)
	
	numColors = len(colors)
	diffsColor = np.zeros([image.shape[0], image.shape[1], numColors], np.int16)
	# Determine per-color how "close" each pixel is
	for i in range(numColors):
		diffsColor[:, :, i] = np.sum(np.abs(image - colors[i]), axis = 2)
	# Line up the shades of gray
	shades = np.stack([black, darkGray, lightGray, white])

	numShades = len(shades)
	diffsShade = np.zeros([image.shape[0], image.shape[1], numShades], np.uint8)
	# Determine per-shade how "close" each pixel is
	for i in range(numShades):
		diffsShade[:, :, i] = np.sum(np.abs(image - shades[i]), axis = 2)
	# Determine which pixels are effectively shades of gray
	lacksColor = (
		np.maximum(np.maximum(image[:, :, 0], image[:, :, 1]), image[:, :, 2]) - \
		np.minimum(np.minimum(image[:, :, 0], image[:, :, 1]), image[:, :, 2])
	) < 32 # <-- (boolean array)
	# (These will get mapped after the colors do)

	# Determine which color has the minimum difference value,
	# and hence is closest to each pixel
	ids = np.argmin(diffsColor, axis = 2)
	# Prepare the final image
	result = colors[ids]
	# Add in the shades of gray, one at a time
	for i in range(numShades):
		replaceWithShade = lacksColor & (np.argmin(diffsShade, axis = 2) == i)
		result[replaceWithShade] = shades[i]
		ids[replaceWithShade] = numColors + i
	# Set the transparent pixels in the ids array to a fixed indicator value
	if transparent:
		ids[whereTransparent] = -1

	return {
		"result": result,
		"ids": ids,
		"dc": diffsColor, # These guys were/are useful for debugging
		"ds": diffsShade,
		"lc": lacksColor
	}
# Downsample the palette of an image,
# and produce a multi-line string with block characters as the pixels
def stringifyImageWithColor(
	image : np.array,
	leftPadding : int = 0,
	darkDelta : int = 0x55,
	BIGSHOT : bool = False
) -> str:
	# Perform the palette conversion and get the color index values we need
	image16Color = convertTo16Color(image, darkDelta)["ids"]
	# If we'll be using half-block characters, make the number of rows even
	if not BIGSHOT and image16Color.shape[0] % 2 == 1:
		image16Color = np.vstack(
			(image16Color, np.zeros([1, image16Color.shape[1]], np.int16) - 1)
		)
	# Color values from colorama, in the same order as the convert function
	colorCodesFore = [
		cr.Fore.RED,
		cr.Fore.GREEN,
		cr.Fore.BLUE,
		cr.Fore.YELLOW,
		cr.Fore.MAGENTA,
		cr.Fore.CYAN,
		cr.Fore.LIGHTRED_EX,
		cr.Fore.LIGHTGREEN_EX,
		cr.Fore.LIGHTBLUE_EX,
		cr.Fore.LIGHTYELLOW_EX,
		cr.Fore.LIGHTMAGENTA_EX,
		cr.Fore.LIGHTCYAN_EX,
		cr.Fore.BLACK,
		cr.Fore.LIGHTBLACK_EX,
		cr.Fore.WHITE,
		cr.Fore.LIGHTWHITE_EX
	]
	colorCodesBack = [
		cr.Back.RED,
		cr.Back.GREEN,
		cr.Back.BLUE,
		cr.Back.YELLOW,
		cr.Back.MAGENTA,
		cr.Back.CYAN,
		cr.Back.LIGHTRED_EX,
		cr.Back.LIGHTGREEN_EX,
		cr.Back.LIGHTBLUE_EX,
		cr.Back.LIGHTYELLOW_EX,
		cr.Back.LIGHTMAGENTA_EX,
		cr.Back.LIGHTCYAN_EX,
		cr.Back.BLACK,
		cr.Back.LIGHTBLACK_EX,
		cr.Back.WHITE,
		cr.Back.LIGHTWHITE_EX
	]
	# Make the string
	s = ' ' * leftPadding
	if BIGSHOT: # Use full block characters only (bigger)
		for y in range(image16Color.shape[0]):
			for x in range(image16Color.shape[1]):
				if image16Color[y, x] < 0: # Handle transparent pixels
					s += "  "
				else:
					s += colorCodesFore[image16Color[y, x]] + "\u2588" * 2
			s += cr.Style.RESET_ALL + '\n'
			# Only pad if we're not the last line
			if y + 1 < image16Color.shape[0]:
				s += ' ' * leftPadding
	else: # Use half-block characters and some logic to get the colors right (small)
		for y in range(0, image16Color.shape[0], 2):
			for x in range(image16Color.shape[1]):
				s += cr.Style.RESET_ALL
			
				if image16Color[y, x] < 0 and image16Color[y + 1, x] < 0:
					s += ' ' # Both pixels are transparent, simple case
				else:
					# Only the top pixel is transparent
					if image16Color[y, x] < 0 and image16Color[y + 1, x] >= 0:
						s += colorCodesFore[image16Color[y + 1, x]] + "\u2584"
					# Only the bottom pixel is transparent
					elif image16Color[y, x] >= 0 and image16Color[y + 1, x] < 0:
						s += colorCodesFore[image16Color[y, x]] + "\u2580"
					# Both pixels have a color (general case)
					else:
						s += colorCodesFore[image16Color[y, x]] \
							+ colorCodesBack[image16Color[y + 1, x]] \
							+ "\u2580"
			s += cr.Style.RESET_ALL + '\n'
			# Only pad if we're not the last line
			if y + 2 < image16Color.shape[0]:
				s += ' ' * leftPadding
		
	return s
# Command line handling
if __name__ == "__main__":
	try:
		source = cv.imread(sys.argv[-1], cv.IMREAD_UNCHANGED)
		if source is None:
			print("Error: Image file not found!\n\t" + sys.argv[-1])
			exit(-1)
	except IndexError as i:
		print("Error: No image file provided!\n\t" + i)
		exit(-1)

	writeOut = False
	BIGSHOT = False
	padding = 0
	dd = 0x55

	if "-w" in sys.argv:
		try:
			outFilename = sys.argv[sys.argv.index("-w") + 1]
			writeOut = True
		except IndexError as i:
			print("Error: No output image filename provided!\n\t" + i)
			exit(-1)

	if "-B" in sys.argv:
		BIGSHOT = True

	if "-p" in sys.argv:
		try:
			padding = int(sys.argv[sys.argv.index("-p") + 1])
		except IndexError as i:
			print("Error: No left padding amount specified!\n\t" + i)
			exit(-1)
		except ValueError as v:
			print("Error: Could not parse padding amount!\n\t" + v)
			exit(-1)

	if "-d" in sys.argv:
		try:
			dd = sys.argv[sys.argv.index("-d") + 1]
			if len(dd) > 2 and dd[:2] == "0x":
				dd = int(dd, base = 16)
			else:
				dd = int(dd)
		except IndexError as i:
			print("Error: No darkness delta amount specified!\n\t" + i)
			exit(-1)
		except ValueError as v:
			print("Error: Could not parse darkness delta amount!\n\t" + v)
			exit(-1)

	s = stringifyImageWithColor(source, padding, dd, BIGSHOT)
	print(s)

	if writeOut:
		f = open(outFilename, 'w')
		f.write(s)
		f.close()
		print("Wrote contents into " + outFilename)

