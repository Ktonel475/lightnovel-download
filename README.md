本项目派生自 [ShqWW/lightnovel-download](https://github.com/ShqWW/lightnovel-download)
<div align="center">
  <img src="assets/logo_big.png" width="300" style="margin-right: 3000px;"/>
</div>

<h1 align="center">
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;EPUB下载器
</h1>

<p align="center">
  <strong>一个简约的轻小说文库 (wenku8.net) 命令行下载工具</strong>
</p>

> [!NOTE]  
> **项目现状：** 考虑到GUI的复杂程度和个人使用习惯，目前已**移除所有 GUI 界面**。本项目现在是一个纯粹的命令行工具（CLI），暂时不提供图形界面版本。

## 功能点

* **防爬避让：** 针对文库吧最近的拦截机制，改用了 `nodriver` (异步 undetected-chromedriver) 进行底层驱动，不再容易被 403。
* **插图识别：** 能够自动区分“彩页”和“普通插图”。彩页会被集中放在书籍开头，还原实体书阅读体验。
* **精简排版：** 生成的 EPUB 目录清晰，支持多线程下载图片。
* **美观反馈：** 命令行界面使用了 `rich` 库，下载进度一目了然。

## 快速开始

### 1. 环境准备

确保你的系统安装了 **Chrome 或 Edge 浏览器**。然后安装依赖：

```bash
pip install -r requirements.txt
```

### 2. 使用说明

直接在终端运行 `ln.py` 即可。

```text
用法: ln.py [-h] [-b BOOK_NO] [-v VOLUME_NO]

轻小说下载器 命令行工具

选项:
  -h, --help            显示帮助信息并退出
  -b BOOK_NO, --book-no BOOK_NO
                        书籍 ID (例如: 2542)
  -v VOLUME_NO, --volume-no VOLUME_NO
                        下载卷号范围 (例如: '1-3', '1,3,5' 或 '1')
```

### 3. 使用示例

* **下载单卷：**

  ```bash
  python ln.py -b 2542 -v 1
  ```

* **下载多卷（非连续）：**

  ```bash
  python ln.py -b 2542 -v 1,3,5
  ```

* **下载范围（连续）：**

  ```bash
  python ln.py -b 2542 -v 1-10
  ```

## EPUB书籍编辑和管理工具推荐

1. [Sigil](https://sigil-ebook.com/)
2. [Calibre](https://www.calibre-ebook.com/)

## 个人碎碎念

本来在搜文库下载器时无意中找到原项目，原项目的epub打包是完全能用的，但是`requests` 及 `beautifulsoups` 在现代满大街都在拦机器人的情况就直接没啦，所以就自己写了个`nodriver` 的。本人习惯用cli就没有特别改GUI(毕竟要重写)，有空的话可能会做。。吧？wwww

