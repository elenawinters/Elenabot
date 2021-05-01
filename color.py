from colorama import Fore, Back, Style
import colorama
colorama.init()

"""
    B stands for background
    S stands for strong

"""


class Trace:
    reset = Style.RESET_ALL
    normal = Style.NORMAL
    generic = Fore.CYAN
    name = Fore.LIGHTYELLOW_EX
    message = Fore.LIGHTGREEN_EX
    type = Fore.LIGHTMAGENTA_EX
    alert = Fore.LIGHTRED_EX
    warn = Fore.LIGHTYELLOW_EX
    id = Fore.LIGHTCYAN_EX
    time = Fore.LIGHTGREEN_EX

    class Styles:
        reset = Style.RESET_ALL
        normal = Style.NORMAL
        bold = Style.BRIGHT
        dim = Style.DIM
        bright = bold

    styles = Styles

    class Black:
        class B:
            s = Back.LIGHTBLACK_EX

            def __str__(self):
                return Back.BLACK
        b = B()
        s = Fore.LIGHTBLACK_EX  # technically gray

        def __str__(self):
            return Fore.BLACK
    black = Black()

    class Red:
        class B:
            s = Back.LIGHTRED_EX

            def __str__(self):
                return Back.RED
        b = B()
        s = Fore.LIGHTRED_EX

        def __str__(self):
            return Fore.RED
    red = Red()

    class Green:
        class B:
            s = Back.LIGHTGREEN_EX

            def __str__(self):
                return Back.GREEN
        b = B()
        s = Fore.LIGHTGREEN_EX

        def __str__(self):
            return Fore.GREEN
    green = Green()

    class Yellow:
        class B:
            s = Back.LIGHTYELLOW_EX

            def __str__(self):
                return Back.YELLOW
        b = B()
        s = Fore.LIGHTYELLOW_EX

        def __str__(self):
            return Fore.YELLOW
    yellow = Yellow()

    class Blue:
        class B:
            s = Back.LIGHTBLUE_EX

            def __str__(self):
                return Back.BLUE
        b = B()
        s = Fore.LIGHTBLUE_EX

        def __str__(self):
            return Fore.BLUE
    blue = Blue()

    class Magenta:
        class B:
            s = Back.LIGHTMAGENTA_EX

            def __str__(self):
                return Back.MAGENTA
        b = B()
        s = Fore.LIGHTMAGENTA_EX

        def __str__(self):
            return Fore.MAGENTA
    magenta = Magenta()

    class Cyan:
        class B:
            s = Back.LIGHTCYAN_EX

            def __str__(self):
                return Back.CYAN
        b = B()
        s = Fore.LIGHTCYAN_EX

        def __str__(self):
            return Fore.CYAN
    cyan = Cyan()

    class White:
        class B:
            s = Back.LIGHTWHITE_EX

            def __str__(self):
                return Back.WHITE
        b = B()
        s = Fore.LIGHTWHITE_EX

        def __str__(self):
            return Fore.WHITE
    white = White()

    # Tuple of all color objects implemented in this class. 36 objects in total.
    tracers = (styles.reset, styles.normal, styles.bold, styles.dim,

               black, black.s, black.b, black.b.s,
               red, red.s, red.b, red.b.s,
               green, green.s, green.b, green.b.s,
               yellow, yellow.s, yellow.b, yellow.b.s,
               blue, blue.s, blue.b, blue.b.s,
               magenta, magenta.s, magenta.b, magenta.b.s,
               cyan, cyan.s, cyan.b, cyan.b.s,
               white, white.s, white.b, white.b.s)


trace = Trace


class Log:  # logging will be handled here for this project. i dont wanna have to use a seperate class for it
    pass


log = Log
