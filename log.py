from termcolor import colored


def success(msg):
    print(colored(msg, 'green'))


def status(msg):
    print(colored(msg, 'blue'))


def warning(msg):
    print(colored(msg, 'yellow'))


def info(msg):
    print(colored(msg, 'white'))
