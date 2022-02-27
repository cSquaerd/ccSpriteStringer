import sys
import cv2 as cv
import numpy as np
import colorama as cr
# Compute (crudely) which basic color each pixel is closest to in RGB space,
# and return a paletted image along with some other metrics
def convertTo16Color(image : np.array, darkDelta : int = 0x55, colorCutoff : int = 32) -> dict:
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
	) < colorCutoff # <-- (boolean array)
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
	colorCutoff : int = 32,
	BIGSHOT : bool = False
) -> str:
	# Perform the palette conversion and get the color index values we need
	image16Color = convertTo16Color(image, darkDelta, colorCutoff)["ids"]
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
callForHelp = "\nRun this program with the -h flag for a help page"
if __name__ == "__main__":
	if "-h" in sys.argv:
		print("Usage: python ccSpriteStringer.py [flags] imageFilename\n")
		print("Flags:")
		print("    -h")
		print("        Show this helpful information page\n")
		print("    -w outputFilename")
		print("        Write the ANSI escape codes and block characters into a text file\n")
		print("    -B")
		print("        Print with full-block characters only (bigger than usual)\n")
		print("    -p offset")
		print("        Print the sprite with `offset` many spaces on the left of each line;")
		print("        Must be greater than 0\n")
		print("    -c")
		print("        Compose a cowfile with the results, with three thoughts lines,")
		print("        and a minimum `padding` value of 8; Requires the -w flag beforehand\n")
		print("    -d darknessDelta")
		print("        Adjust the value by which the dark colors are represented;")
		print("        The default internal value is 0x55, or 85 in decimal;")
		print("        Must be greater than 0 and less than 255\n")
		print("    -D [begin end step]")
		print("        Run through a range of darknessDelta values and show their results;")
		print("        The default values are `begin`=16, `end`=136, and `step`=8;")
		print("        Useful for when the default darknessDelta does not yield")
		print("        satisfactory results; Ignores the -w flag;")
		print("        `begin` must be less than `end`, and both must be between 0 and 255")
		exit(0)

	try:
		source = cv.imread(sys.argv[-1], cv.IMREAD_UNCHANGED)
		if source is None:
			print("Error: Image file not found!\n\t" + sys.argv[-1])
			print(callForHelp)
			exit(-1)
	except IndexError as i:
		print("Error: No image file provided!\n\t" + str(i))
		print(callForHelp)
		exit(-1)

	writeOut = False
	makeCow = False
	BIGSHOT = False
	padding = 0
	dd = 0x55
	cc = 32

	if "-w" in sys.argv:
		try:
			outFilename = sys.argv[sys.argv.index("-w") + 1]
			writeOut = True
		except IndexError as i:
			print("Error: No output image filename provided!\n\t" + str(i))
			print(callForHelp)
			exit(-1)

	if "-B" in sys.argv:
		BIGSHOT = True

	if "-p" in sys.argv:
		try:
			padding = int(sys.argv[sys.argv.index("-p") + 1])
		except IndexError as i:
			print("Error: No left padding amount specified!\n\t" + str(i))
			print(callForHelp)
			exit(-1)
		except ValueError as v:
			print("Error: Could not parse padding amount!\n\t" + str(v))
			print(callForHelp)
			exit(-1)

	if "-c" in sys.argv:
		if not writeOut:
			print("Warning: No cowfile will be created as the -w flag is not set")
		else:
			makeCow = True
			cowFilename = outFilename.split('.')[0] + ".cow"
			padding = max(8, padding)
	if "-g" in sys.argv:
		try:
			cc = int(sys.argv[sys.argv.index("-g") + 1], base = 0)
		except IndexError as i:
			print("Error: No color cutoff amount specified!\n\t" + str(i))
			print(callForHelp)
			exit(-1)
		except ValueError as v:
			print("Error: Could not parse color cutoff amount!\n\t" + str(v))
			print(callForHelp)
			exit(-1)

	if "-d" in sys.argv:
		try:
			dd = int(sys.argv[sys.argv.index("-d") + 1], base = 0)
		except IndexError as i:
			print("Error: No darkness delta amount specified!\n\t" + str(i))
			print(callForHelp)
			exit(-1)
		except ValueError as v:
			print("Error: Could not parse darkness delta amount!\n\t" + str(v))
			print(callForHelp)
			exit(-1)

	if "-D" in sys.argv:
		i = sys.argv.index("-D")
		if len(sys.argv) - 1 > i + 3:
			try:
				begin = int(sys.argv[i + 1], base = 0)
				end = int(sys.argv[i + 2], base = 0)
				step = int(sys.argv[i + 3], base = 0)
			except ValueError as v:
				print("Error: Could not parse darkness range parameter!\n\t" + str(v))
				print(callForHelp)
				exit(-1)
			count = (end - begin) // step + 1
		else:
			begin = 0x10
			count = 16
			step = 8
		for d in (np.arange(count) * step) + begin:
			print("darknessDelta:", d, "(0x" + format(d, "x") + ")")
			print(stringifyImageWithColor(source, padding, d, cc, BIGSHOT))
		exit(0)

	s = stringifyImageWithColor(source, padding, dd, cc, BIGSHOT)
	print(s)

	if writeOut:
		f = open(outFilename, 'w')
		f.write(s)
		f.close()
		print("Wrote contents into " + outFilename)
		if makeCow:
			firstLine  = "    $thoughts   " + s.split('\n')[0][8:]
			secondLine = "     $thoughts  " + s.split('\n')[1][8:]
			thirdLine  = "      $thoughts " + s.split('\n')[2][8:]

			f = open(cowFilename, 'w')
			f.write(
				"#\n# Put a witty comment here\n#\n$the_cow = <<EOC;\n" \
				+ firstLine + '\n' + secondLine + '\n' + thirdLine + '\n' \
				+ '\n'.join(s.split('\n')[3:])+ "EOC\n"
			)
			f.close()
			print("Created cowfile at " + cowFilename + ';')

