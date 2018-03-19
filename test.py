import argparse
from math import sqrt

def area_of_triangle():
    parser = argparse.ArgumentParser(prog="Area of Triangle")
    parser.add_argument("-v", "--verbose", type=int, help="turn verbosity ON/OFF", choices=[0,1])
    parser.add_argument("-a", "--sideA", type=float, help="side A of triangle")
    parser.add_argument("-b", "--sideB", type=float, help="side B of triangle")
    parser.add_argument("-c", "--sideC", type=float, help="side C of triangle")
    args = parser.parse_args()

    s = (args.sideA + args.sideB + args.sideC)/2
    area_hero = sqrt(s*(s-args.sideA)*(s-args.sideB)*(s-args.sideC))

    if args.verbose==1:
        print("for triangle of sides {:<6f}, {:<6f}, {:<6f}, ".format(args.sideA, args.sideB, args.sideC))
        print("the semi perimeter is {:<6f} while the area is {:<6f}".format(s, area_hero))
    else:
        print("area = {:<6f}".format(area_hero))

if __name__ == "__main__":
    area_of_triangle()
