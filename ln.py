import asyncio
from Editor import Editor
import argparse


def parse_args():
    """Parse input arguments."""
    parser = argparse.ArgumentParser(description="config")
    parser.add_argument("--book_no", default=None, type=str)
    parser.add_argument("--volume_no", default=None, type=str)
    parser.add_argument(
        "--no_input", action="store_true", help="Skip interactive input"
    )
    args = parser.parse_args()
    return args


def downloader_router(root_path, book_no, volume_no):
    # Null result handling (if volume_no is empty or None)
    if not volume_no:
        asyncio.run(run_downloader(book_no, None, root_path))
        return

    # Ensure we are working with a string for parsing logic
    raw_val = str(volume_no).replace(" ", "")

    if "-" in raw_val or "," in raw_val:
        volumes_to_process = []

        if "," in raw_val:
            volumes_to_process = [
                int(v) for v in raw_val.split(",") if v.strip().isdigit()
            ]
        elif "-" in raw_val:
            try:
                start, end = map(int, raw_val.split("-"))
                volumes_to_process = list(range(start, end + 1))
            except ValueError:
                print(f"Error: Invalid range format '{raw_val}'")
                return

        print(f"Detected multiple volumes: {volumes_to_process}")

        for v in volumes_to_process:
            print(f"Processing volume: {v}...")
            asyncio.run(run_downloader(book_no, v, root_path))

    else:
        # Single number handling
        try:
            v_int = int(raw_val)
            asyncio.run(run_downloader(book_no, v_int, root_path))
        except ValueError:
            print(f"Error: '{raw_val}' is not a valid number.")


async def run_downloader(book_no, volume_no, root_path):
    downloader = await Editor.create(
        root_path=root_path, book_no=str(book_no), volume_no=volume_no
    )
    if downloader:
        await downloader.run_full_export()


if __name__ == "__main__":
    args = parse_args()
    root_dir = "out"

    # Scenario 1: Command line arguments are provided
    if args.book_no:
        print(f"Running in CLI mode for Book: {args.book_no}")
        downloader_router(
            root_path=root_dir, book_no=args.book_no, volume_no=args.volume_no
        )

    # Scenario 2: No arguments, or explicitly asked for interactive mode
    elif not args.no_input:
        while True:
            try:
                book_input = input("\n请输入书籍号 (输入 q 退出)：").strip()
                if book_input.lower() == "q":
                    break
                if not book_input:
                    continue

                volume_input = input(
                    "请输入卷号 (查看目录不输入直接回车，多卷用逗号或连字符)："
                ).strip()

                downloader_router(
                    root_path=root_dir, book_no=book_input, volume_no=volume_input
                )
            except KeyboardInterrupt:
                print("\n程序已停止。")
                break
    else:
        print("Error: No book_no provided and --no_input is active.")
