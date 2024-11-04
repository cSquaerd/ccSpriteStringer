import cv2 as cv
import numpy as np
from argparse import ArgumentParser, RawTextHelpFormatter

def adjust_brightness_contrast(in_image : np.array, contrast : float, brightness : int) -> np.array:
	if in_image.shape[2] > 3:
		contrast = np.array([contrast, contrast, contrast, 1.])
		brightness = np.array([brightness, brightness, brightness, 0])
	
	return np.round(np.clip(contrast * in_image.astype(np.int16) + brightness, 0, 255)).astype(np.uint8)

def rgb_to_twofiftysix(in_image : np.array, grayify : bool = True) -> np.array:
	SIX_BIT_COLOR_SCALAR = int(255 / 5) # == 51
	IMAGE_DTYPE = np.uint8
	GRAY_DELTA_LIMIT = 5
	BLACK_UPPER_LIMIT = 8
	WHITE_LOWER_LIMIT = 248
	ALPHA_CHANNEL = 3
	
	out_image = np.zeros(in_image.shape[:2], dtype = IMAGE_DTYPE)

	is_transparent = in_image.shape[2] > ALPHA_CHANNEL
	if is_transparent: # possible
		where_transparent = np.where(in_image[:, :, ALPHA_CHANNEL] == 0)
		in_image = in_image[:, :, :ALPHA_CHANNEL] # lop off the alpha channel
	else: # impossible
		where_transparent = np.where(in_image < 0)

	# Step 1: Cast to colors
	out_image[:, :] = 16 + np.sum( # Color channels are blue, green, red,
		np.round(in_image / SIX_BIT_COLOR_SCALAR).astype(IMAGE_DTYPE) * np.array([1, 6, 36]), axis = 2
	) # and the formula for the six-bit cube is 16 + blue + 6 * green + 36 * red, for 0 <= blue, green, red <= 5

	# Step 2: handle grays
	if grayify:
		where_gray = np.where(
			(np.max(in_image, axis = 2) - np.min(in_image, axis = 2) < GRAY_DELTA_LIMIT)
			& (np.min(in_image, axis = 2) >= BLACK_UPPER_LIMIT) & (np.max(in_image, axis = 2) < WHITE_LOWER_LIMIT)
		)

		out_image[where_gray] = ((np.round(np.average(in_image, axis = 2)) - 8) // 10 + 232)[where_gray]
	
	# Step 3: handle transparency
	out_image[where_transparent] = 0

	return out_image

def twofiftysix_to_string(indexed_image : np.array) -> str:
	if indexed_image.shape[0] % 2 == 1:
		indexed_image = np.vstack([indexed_image, np.zeros(indexed_image.shape[1], np.uint8)])

	s = ""
	for y in range(0, indexed_image.shape[0], 2):
		for x in range(indexed_image.shape[1]):
			if indexed_image[y, x] == 0 and indexed_image[y + 1, x] == 0:
				s += ' '
			elif indexed_image[y, x] == 0:
				s += "\x1B[38;5;{:d}m\u2584\x1B[0m".format(indexed_image[y + 1, x])
			elif indexed_image[y + 1, x] == 0:
				s += "\x1B[38;5;{:d}m\u2580\x1B[0m".format(indexed_image[y, x])
			else:
				s += "\x1B[38;5;{:d};48;5;{:d}m\u2580\x1B[0m".format(indexed_image[y, x], indexed_image[y + 1, x])
		s += '\n'

	return s

def interactive_bcg(sprite : np.array, contrast_0 : float, brightness_0 : int, nogray_0 : bool):
	running = True
	contrast = contrast_0
	brightness = brightness_0
	nogray = nogray_0
	modified = True

	while running:
		if modified:
			print(
				twofiftysix_to_string(
					rgb_to_twofiftysix(adjust_brightness_contrast(sprite, contrast, brightness), not nogray)
				)
			)
			print(
				'\n'.join(
					[
						"No Grayscale: {!r}".format(nogray),
						"Brightness: {:4d}".format(brightness),
						"Contrast: {:6.2F}".format(contrast)
					]
				)
			)
			modified = False

		command = input("Enter a command ('h' for help): ")

		if command in ('h', "help"):
			print(
				'\n'.join(
					[
						"'b [int]': set brightness", "'bp': increment brightness by 5", "'bm': decrement brightness by 5",
						"'c [float]': set contrast", "'cp': increment contrast by 0.05", "'cm': decrement contrast by 0.05",
						"'g': toggle No Grayscale flag", "'r': reset values", "'o': show original image",
						"'h': print this help listing", "'q': quit program"
					]
				) + '\n'
			)

		elif command.split(' ')[0] in ('b', "bright", "brightness"):
			try:
				brightness = int(command.split(' ')[1])
				modified = True
			except ValueError as ve:
				print("Error: Bad Input <{!r}>".format(ve))

		elif command.split(' ')[0] in ('c', "con", "contrast"):
			try:
				contrast = float(command.split(' ')[1])
				modified = True
			except ValueError as ve:
				print("Error: Bad Input <{!r}>".format(ve))

		elif command == "bp":
			brightness += 5
			modified = True

		elif command == "bm":
			brightness -= 5
			modified = True

		elif command == "cp":
			contrast += 0.05
			modified = True

		elif command == "cm":
			contrast -= 0.05
			modified = True

		elif command in ('g', "gray", "grayscale"):
			nogray = not nogray
			modified = True

		elif command in ('r', "reset"):
			brightness = brightness_0
			contrast = contrast_0
			nogray = nogray_0
			modified = True

		elif command in ('o', "original"):
			print(twofiftysix_to_string(rgb_to_twofiftysix(sprite)))

		elif command in ('q', "quit"):
			return


def main():
	parser = ArgumentParser(
		description = "Convert PNGs (transparent or otherwise) into 256-color ANSI text sprites",
		formatter_class = RawTextHelpFormatter
	)

	parser.add_argument(
		"sprite", help = "Path to sprite image file"
	)

	parser.add_argument(
		"-n", "--nogray", action = "store_true",
		help = "Do not detect gray pixels and do not map them to the 24 gray levels"
	)

	parser.add_argument(
		"-B", "--bigshot", action = "store_true",
		help = "Use double full blocks instead of half blocks, doubling the sprite size"
	)

	parser.add_argument(
		"-c", "--contrast", action = "store", default = 1.0,
		help = "Adjust the contrast before casting colors to 6-bit"
	)

	parser.add_argument(
		"-b", "--brightness", action = "store", default = 0,
		help = "Adjust the brightness before casting colors to 6-bit"
	)

	parser.add_argument(
		"-i", "--interactive", action = "store_true",
		help = "Interactively tweak brightness, contrast, and gray pixel usage"
	)

	argv = parser.parse_args()

	try:
		sprite = cv.imread(argv.sprite, cv.IMREAD_UNCHANGED)
	
		if argv.interactive:
			interactive_bcg(sprite, float(argv.contrast), int(argv.brightness), argv.nogray)
		elif argv.contrast != 1. or argv.brightness != 0:
			print(
				twofiftysix_to_string(
					rgb_to_twofiftysix(
						adjust_brightness_contrast(sprite, float(argv.contrast), int(argv.brightness)), not argv.nogray
					)
				)
			)
		else:
			print(
				twofiftysix_to_string(
					rgb_to_twofiftysix(sprite, not argv.nogray) #, parser.bigshot
				)
			)
	
	except FileNotFoundError as fnfe:
		print("Error! {:s} could not be opened! <{:s}>".format(argv.sprite, str(fnfe)))
		exit(-1)

	except AttributeError as ae:
		print("Error! Argument parsing failed! <{:s}>".format(str(ae)))
	
if __name__ == "__main__":
	main()

