import argparse
import behavior as m


def main():
    ap = argparse.ArgumentParser(description="行为树中断与恢复")
        ap.add_argument("--events", required=True)
        ap.add_argument("--out", required=True)
    a = ap.parse_args()
        print("TODO")


if __name__ == "__main__":
    main()
