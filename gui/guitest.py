import multiprocessing
import sys
from PIL import Image
from pystray import Icon, Menu, MenuItem
import webview

if sys.platform == 'darwin':
  ctx = multiprocessing.get_context('spawn')
  Process = ctx.Process
  Queue = ctx.Queue
else:
  Process = multiprocessing.Process
  Queue = multiprocessing.Queue

webview_process = None


def run_webview():
  webview.create_window(
      'My HTML App', 'https://pywebview.flowrl.com/hello'
  )  # Or point to a local index.html file
  webview.start()


if __name__ == '__main__':

  def start_webview_process():
    global webview_process
    webview_process = Process(target=run_webview)
    webview_process.start()

  def on_open(icon, item):
    global webview_process
    if not webview_process or not webview_process.is_alive():
      start_webview_process()

  def on_exit(icon, item):
    icon.stop()
    if webview_process and webview_process.is_alive():
      webview_process.terminate()

  image = Image.open('assets/logo.png')
  menu = Menu(MenuItem('Open HTML UI', on_open), MenuItem('Exit', on_exit))
  icon = Icon('PystrayHTMLApp', image, menu=menu)

  start_webview_process()
  icon.run()