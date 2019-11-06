"""Direct users to the new resmoke"""

import sys


def main():
    print("Resmoke is now a pip package. You can install it by running pip "
          "install -e buildscripts/resmoke and execute resmoke with python -m "
          "resmokelib.cli or if using a virtualenv simply using the command "
          "'resmoke'")
    sys.exit(1)


if __name__ == '__main__':
    main()
