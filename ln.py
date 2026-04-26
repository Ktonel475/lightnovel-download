import asyncio
from Editor import Editor
import argparse
import sys
import nodriver as uc
import os
from rich.console import Console
from rich.panel import Panel


def get_args():
    parser = argparse.ArgumentParser(description="Book Downloader CLI", add_help=True)

    parser.add_argument("-b", "--book-no", type=str, help="The ID of the book")

    parser.add_argument("-v", "--volume-no", type=str, help="Volume range (e.g., 1-3)")

    return parser.parse_args(), parser


async def run_downloader(book_no, vol_no, root_path):
    # Console UI initalize
    console = Console()

    raw_val = str(vol_no).replace(" ", "")
    try:
        if "-" in raw_val:
            start, end = map(int, raw_val.split("-"))
            vols = list(range(start, end + 1))
        elif "," in raw_val:
            vols = [int(v) for v in raw_val.split(",") if v.strip().isdigit()]
        else:
            vols = [int(raw_val)]
    except ValueError:
        console.print(f"[bold red]错误:[/bold red] 卷号格式无效: {vol_no}")
        return

    browser = await uc.start()

    try:
        editor = Editor(root_path, browser, book_no)
        title, author = await editor.init_book_info()

        if not title:
            console.print("[bold red]错误:[/bold red] 无法获取书籍信息。")
            return

        info_display = (
            f"[bold magenta]书名:[/bold magenta] {title}\n"
            f"[bold cyan]作者:[/bold cyan] {author}\n"
            f"[bold green]目标:[/bold green] 下载第 {vol_no} 卷 (共 {len(vols)} 个任务)"
        )
        console.print(
            Panel(info_display, title="[yellow]确认下载详情[/yellow]", expand=False)
        )

        console.print("\n确认下载吗？ [[bold]Y/n[/bold]] ", end="")

        user_input = await asyncio.to_thread(sys.stdin.readline)
        choice = user_input.strip().lower()

        if choice == "n":
            console.print("[red]已取消。[/red]")
            return

        for v in vols:
            console.rule(f"[bold yellow]正在处理第 {v} 卷[/bold yellow]")
            await editor.process_single_volume(v)
    except Exception as e:
        console.print(f"[bold red]发生错误:[/bold red] {e}")

    finally:
        # Hide technical cleanup messages
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")

        try:
            browser.stop()
            await asyncio.sleep(1)
        except:
            pass
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        console.print("\n[bold green]✔ 任务已全部完成。[/bold green]")


if __name__ == "__main__":
    args, parser = get_args()
    root_dir = "out"

    if not args.book_no:
        print("Error: Missing required argument '-b' or '--book-no'\n")
        parser.print_help()
        sys.exit(1)

    asyncio.run(
        run_downloader(root_path=root_dir, book_no=args.book_no, vol_no=args.volume_no)
    )
