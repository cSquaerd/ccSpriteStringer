# ccSpriteStringer
## Turns PNG sprites into strings of 256-color unicode block characters
### *(Examples can be found at my other repo, [ccCowsprites](https://github.com/cSquaerd/ccCowsprites/tree/master/cowfiles))*

## Package installation (example): `pip install --user --break-system-packages .`
*(That second flag is needed on Arch systems, even though it's all going to `~/.local/lib/`)*

## Usage (raw): `python ccSpriteStringer256.py [flags] imageFilename`
## Usage (package): `python -m spritestringer [flags] imageFilename`

## Flags:
```
  -h, --help            show this help message and exit
  -b, --brightness B (int)
                        Adjust the brightness before casting colors to 6-bit
                          (-255 <= B <= 255)
  -c, --contrast C (float)
                        Adjust the contrast before casting colors to 6-bit
                          (C >= 0)
  -n, --nogray          Do not explicitly detect gray pixels to map to the 24 gray levels
  -i, --interactive     Interactively tweak brightness, contrast, and gray pixel usage
  -B, --bigshot         Use double full blocks instead of half blocks,
                        doubling the sprite size
                          (Ignored in interactive mode)
  -C, --cowfile         Create a cowfile representation of the sprite
                          (File will be created in the working directory
                          with the same basename as the sprite image)
                          (Ignored in interactive mode)
  -m, --cowfile_comment COMMENT (str)
                        Comment to put at the top of the cowfile if in cowfile mode
```

