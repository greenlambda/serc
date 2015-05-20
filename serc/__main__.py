import serc
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('specfile', type=argparse.FileType('r'))

if __name__ == '__main__':
    args = parser.parse_args()
    if args.specfile is not None:
        serializer = serc.JsonToCSerializer(args.specfile)
        serializer.parse()
