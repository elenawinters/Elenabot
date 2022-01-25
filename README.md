# Elenabot

This is a Twitch bot made by myself, Elena, for personal use. This may be merged in with the Stitch project down the line.

## The -OO flag

It is recommended you run this project with the -OO flag provided to the interpreter.

```sh
python3 -OO bot.py
```

### What is the -OO flag?

Python has optimization flags suprisingly. There are 2 of them

- The -O flag (O1)
    This tells the interpreter/compiler to replace `__debug__` with 0, and to ignore assertions.
- The -OO flag (O2)
    This tells the interpreter/compiler to do that same as O1, and also ignore docstrings.

This project uses debug flags and docstrings. It is recommended you use -OO so that these are ignored in production environments

## Requirements

This project uses features from Python 3.10.
