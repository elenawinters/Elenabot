# Elenabot

This is a Twitch bot made by myself, Elena, for personal use.

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
    This does the same as O1, and also ignores docstrings.

This project uses debug flags and docstrings. It is recommended you use -OO so that these are ignored in production environments

## Requirements

This project is currently being developed in Python 3.13.
