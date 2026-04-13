#!/usr/bin/python
# -*- coding:utf-8 -*-

import asyncio
import nodriver as uc
from bs4 import BeautifulSoup
import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from utils import *
from rich.progress import track as tqdm
import shutil
from PIL import Image
import zipfile

lock = threading.RLock()


class Editor(object):
    def __init__(self, root_path, book_no="0000", volume_no=1):
        # Sync attributes
        self.url_head = "https://www.wenku8.net"
        self.main_page = f"{self.url_head}/book/{book_no}.htm"
        self.color_chap_name = "插图"
        self.color_page_name = "彩页"
        self.html_buffer = dict()
        self.img_url_map = dict()
        self.volume_no = volume_no
        self.epub_path = root_path
        self.max_thread_num = 8
        self.pool = ThreadPoolExecutor(self.max_thread_num)

        # State management
        self.browser = None
        self.is_color_page = True
        self.temp_path = ""

    @classmethod
    async def create(cls, root_path, book_no="0000", volume_no=1):
        """Async factory to handle nodriver startup and initial scrapes"""
        self = cls(root_path, book_no, volume_no)

        # Start nodriver with a persistent profile to help with Cloudflare
        self.browser = await uc.start()

        # 1. Scrape Main Page
        main_html = await self.get_html(self.main_page)
        match = re.search(r"<a href=\"(.*?)\">小说目录</a>", main_html)

        if not match:
            print("脚本被拦截或找不到目录链接")
            await self.browser.stop()
            return None

        self.cata_page = self.url_head + match.group(1)

        # 2. Scrape Catalog
        cata_html = await self.get_html(self.cata_page)
        bf = BeautifulSoup(cata_html, "html.parser")

        title_tag = bf.find("div", {"id": "title"})
        self.title = title_tag.text if title_tag else "Unknown_Title"

        author_tag = bf.find("div", {"id": "info"})
        self.author = (
            author_tag.text[3:]
            if author_tag and len(author_tag.text) > 3
            else "Unknown_Author"
        )

        # 3. Handle Cover URL
        cover_list = re.findall(r"<img src=\"(.*?)\"", main_html)
        self.cover_url = (
            cover_list[1]
            if len(cover_list) > 1
            else (cover_list[0] if cover_list else "")
        )

        # 4. Setup Paths
        safe_title = check_chars(self.title)
        self.temp_path = os.path.join(
            self.epub_path, f"temp_{safe_title}_{self.volume_no}"
        )

        return self

    async def get_html(self, url):
        """Uses the shared nodriver instance to fetch HTML"""
        page = await self.browser.get(url)
        # Random wait to mimic human reading and satisfy Cloudflare
        await page.wait(3)
        return await page.get_content()

    def get_image(self, is_gui=False, signal=None):
        for url in self.img_url_map.keys():
            self.pool.submit(self.get_html_img, url)
        img_path = self.img_path
        if is_gui:
            len_iter = len(self.img_url_map.items())
            signal.emit("start")
            for i, (img_url, img_name) in enumerate(self.img_url_map.items()):
                content = self.get_html_img(img_url)
                with open(img_path + f"/{img_name}.jpg", "wb") as f:
                    f.write(content)  # 写入二进制内容
                signal.emit(int(100 * (i + 1) / len_iter))
            signal.emit("end")
        else:
            for img_url, img_name in tqdm(self.img_url_map.items()):
                content = self.get_html_img(img_url)
                with open(img_path + f"/{img_name}.jpg", "wb") as f:
                    f.write(content)  # 写入二进制内容

    def get_cover(self, is_gui=False, signal=None):
        textfile = os.path.join(self.text_path, "cover.xhtml")
        img_w, img_h = 300, 300
        try:
            imgfile = os.path.join(self.img_path, "00.jpg")
            img = Image.open(imgfile)
            img_w, img_h = img.size
            signal_msg = (imgfile, img_h, img_w)
            if is_gui:
                signal.emit(signal_msg)
        except Exception as e:
            print(e)
            print("没有封面图片，请自行用第三方EPUB编辑器手动添加封面")
        img_htmls = get_cover_html(img_w, img_h)
        with open(textfile, "w+", encoding="utf-8") as f:
            f.writelines(img_htmls)

    def get_html_img(self, url):
        """Images usually don't need nodriver, requests is faster for bulk"""
        if url in self.html_buffer:
            return self.html_buffer[url]

        headers = {"User-Agent": "Mozilla/5.0...", "Referer": self.url_head}
        while True:
            try:
                import requests

                req = requests.get(url, headers=headers, timeout=10)
                with lock:
                    self.html_buffer[url] = req.content
                return req.content
            except:
                continue

    def make_folder(self):
        os.makedirs(self.temp_path, exist_ok=True)
        self.text_path = os.path.join(self.temp_path, "OEBPS/Text")
        os.makedirs(self.text_path, exist_ok=True)
        self.img_path = os.path.join(self.temp_path, "OEBPS/Images")
        os.makedirs(self.img_path, exist_ok=True)

    def get_toc(self):
        if self.is_color_page:
            ind = self.volume["chap_names"].index(self.color_chap_name)
            self.volume["chap_names"].pop(ind)
        toc_htmls = get_toc_html(self.title, self.volume["chap_names"])
        textfile = self.temp_path + "/OEBPS/toc.ncx"
        with open(textfile, "w+", encoding="utf-8") as f:
            f.writelines(toc_htmls)

    def get_content(self):
        num_chap = len(self.volume["chap_names"])
        num_img = len(os.listdir(self.img_path))
        content_htmls = get_content_html(
            self.title + "-" + self.volume["book_name"],
            self.author,
            num_chap,
            num_img,
            self.is_color_page,
        )
        textfile = self.temp_path + "/OEBPS/content.opf"
        with open(textfile, "w+", encoding="utf-8") as f:
            f.writelines(content_htmls)

    def get_epub_head(self):
        mimetype = "application/epub+zip"
        mimetypefile = self.temp_path + "/mimetype"
        with open(mimetypefile, "w+", encoding="utf-8") as f:
            f.write(mimetype)
        metainf_folder = os.path.join(self.temp_path, "META-INF")
        os.makedirs(metainf_folder, exist_ok=True)
        container = metainf_folder + "/container.xml"
        container_htmls = get_container_html()
        with open(container, "w+", encoding="utf-8") as f:
            f.writelines(container_htmls)

    def get_epub(self):
        epub_file = (
            self.epub_path
            + "/"
            + check_chars(self.title)
            + "-"
            + check_chars(self.volume["book_name"])
            + ".epub"
        )
        with zipfile.ZipFile(epub_file, "w", zipfile.ZIP_DEFLATED) as zf:
            for dirpath, _, filenames in os.walk(self.temp_path):
                fpath = dirpath.replace(
                    self.temp_path, ""
                )  # 这一句很重要，不replace的话，就从根目录开始复制
                fpath = fpath and fpath + os.sep or ""
                for filename in filenames:
                    zf.write(os.path.join(dirpath, filename), fpath + filename)
        shutil.rmtree(self.temp_path)
        return epub_file

    async def get_index_url(self):
        self.volume = {"chap_urls": [], "chap_names": []}
        volume_title_list, chap_names_list, chap_urls_list = await self.get_chap_list(
            is_print=False
        )

        if len(volume_title_list) < self.volume_no:
            print("输入卷号超过实际卷数！")
            return False

        idx = self.volume_no - 1
        self.volume["chap_names"] = chap_names_list[idx]
        self.volume["chap_urls"] = chap_urls_list[idx]
        self.volume["book_name"] = volume_title_list[idx]
        return True

    async def get_chap_list(self, is_print=True):
        cata_html = await self.get_html(self.cata_page)
        bf = BeautifulSoup(cata_html, "html.parser")
        chap_table = bf.find("table", {"class": "css"})
        if not chap_table:
            return [], [], []

        volume_title_list, chap_urls_list, chap_names_list = [], [], []

        rows = chap_table.find_all("td")
        for td in rows:
            cls = td.get("class", [])
            if "vcss" in cls:
                volume_title_list.append(td.text)
                chap_urls_list.append([])
                chap_names_list.append([])
            elif "ccss" in cls:
                a_tag = td.find("a")
                if a_tag:
                    chap_names_list[-1].append(td.text.strip())
                    chap_urls_list[-1].append(
                        self.cata_page.replace("index.htm", a_tag["href"])
                    )

        return volume_title_list, chap_names_list, chap_urls_list

    async def get_chap_text(self, url, chap_name, is_color=False):
        print(f"Downloading: {chap_name}")
        content_html = await self.get_html(url)
        bf = BeautifulSoup(content_html, "html.parser")
        text_with_head = bf.find("div", {"id": "content"})
        text_chap = ""

        if is_color:
            img_tags = text_with_head.find_all("img", {"class": "imagecontent"})
            for img in img_tags:
                src = img.get("src")
                self.img_url_map[src] = str(len(self.img_url_map)).zfill(2)
                text_chap += f"[img:{self.img_url_map[src]}]\n"
        else:
            # Clean up the text
            for br in text_with_head.find_all("br"):
                br.replace_with("\n")
            text_chap = text_with_head.get_text()

        return text_chap

    async def run_full_export(self):
        """Main orchestrator for the class"""
        if not await self.get_index_url():
            return

        self.make_folder()
        img_strs = []
        text_no = 0

        # Process chapters
        for chap_name, chap_url in zip(
            self.volume["chap_names"], self.volume["chap_urls"]
        ):
            is_color = chap_name == self.color_chap_name
            text = await self.get_chap_text(chap_url, chap_name, is_color)

            if is_color:
                text_html_color = text2htmls(self.color_page_name, text)
            else:
                text_html = text2htmls(chap_name, text)
                filename = os.path.join(
                    self.text_path, f"{str(text_no).zfill(2)}.xhtml"
                )
                with open(filename, "w", encoding="utf-8") as f:
                    f.writelines(text_html)
                text_no += 1

        # Finalize
        self.get_image()  # Sync multi-threading
        self.get_cover()
        self.get_toc()
        self.get_content()
        self.get_epub_head()
        epub = self.get_epub()

        await self.browser.stop()
        print(f"Finished: {epub}")


# --- Core Logic to Run the Class ---
async def main():
    downloader = await Editor.create(
        root_path="./downloads", book_no="2451", volume_no=1
    )
    if downloader:
        await downloader.run_full_export()


if __name__ == "__main__":
    uc.loop().run_until_complete(main())
