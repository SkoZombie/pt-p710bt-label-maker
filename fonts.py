import glob

# Common font directories
font_dirs = [
    "/usr/share/fonts",  # Linux
    "/usr/local/share/fonts",
    "~/.fonts",
    "C:\\Windows\\Fonts",  # Windows
    "/System/Library/Fonts",  # macOS
    "/Library/Fonts"
]

# Find .ttf and .otf fonts
font_files = []
for directory in font_dirs:
    font_files.extend(glob.glob(directory + "/**/*.ttf", recursive=True))
    font_files.extend(glob.glob(directory + "/**/*.otf", recursive=True))

# Display found fonts
for font in sorted(font_files):
    print(font)

