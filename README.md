# ccSpriteStringer
## Turns PNG sprites into strings of 16-color unicode block characters

## Usage: `python ccSpriteStringer.py [flags] imageFilename`

## Flags:
* `-h`
	* Show this helpful information page

* `-w outputFilename`
	* Write the ANSI escape codes and block characters into a text file

* `-B`
	* Print with full-block characters only (bigger than usual)

* `-p offset`
	* Print the sprite with `offset` many spaces on the left of each line;
	Must be greater than 0

* `-c`
	* Compose a cowfile with the results, with three thoughts lines,
	and a minimum `padding` value of 8; Requires the -w flag beforehand

* `-d darknessDelta`
	* Adjust the value by which the dark colors are represented;
	The default internal value is 0x55, or 85 in decimal;
	Must be greater than 0 and less than 255

* `-D [begin end step]`
	* Run through a range of darknessDelta values and show their results;
	The default values are `begin`=16, `end`=136, and `step`=8;
	Useful for when the default darknessDelta does not yield
	satisfactory results; Ignores the -w flag;
	`begin` must be less than `end`, and both must be between 0 and 255
