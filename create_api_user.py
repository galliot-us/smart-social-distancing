import argparse

from libs.utils.auth import create_api_user

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', required=True)
    parser.add_argument('--password', required=True)
    args = parser.parse_args()
    create_api_user(args.user, args.password)
