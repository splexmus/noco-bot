import argparse

from .app import RobotScreenApplication


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the NOCO robot face display")
    parser.add_argument(
        "--windowed",
        action="store_true",
        help="open a resizable window instead of fullscreen",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="cycle through expressions without microphone or AI services",
    )
    args = parser.parse_args()

    RobotScreenApplication(
        fullscreen=not args.windowed,
        demo=args.demo,
    ).run()


if __name__ == "__main__":
    main()
