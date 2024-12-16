# Process:
# Setup letterIndex from 0 till length of text
# Iterate through rows and cols:
# Get pixel and extract R, G, B
# R = (R & 0xFE) | ((text[letterIndex] >> (7 - bitIndex++) & 0x1)
# if (bitIndex > 7) letterIndex++ bitIndex = 0;
# if letterIndex > length, break;
# Repeat for G and B