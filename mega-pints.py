from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests as req
import time
from random import choice
import os
from tqdm.auto import tqdm
import shutil
from bs4 import BeautifulSoup
from PIL import Image
import io

columns = shutil.get_terminal_size().columns

uagent = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/72.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:61.0) Gecko/20100101 Firefox/72.0',
    'Mozilla/5.0 (X11; Linux i586; rv:31.0) Gecko/20100101 Firefox/72.0',
]

headers = {'User-Agent': choice(uagent)} if uagent else {}

mobile_emulation = {"deviceName": "Nexus 10"}

class Pints:

    def __init__(self, search, amount, headless=True):
        self.opt = Options()
        # self.opt.add_experimental_option('mobileEmulation', mobile_emulation)
        self.opt.add_argument('--incognito')
        if headless:
            self.opt.add_argument('--headless')
        self.opt.add_argument('--disable-gpu')
        self.opt.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.search = search
        self.amount = amount

        self.link = 'https://id.pinterest.com/search/pins/?q=%s&rs=typed' % (self.search)

        try:
            self.alf = webdriver.Chrome(options=self.opt)
        except Exception as e:
            print("Terjadi kesalahan:", str(e))
            self.quit()
            exit()

        self.alf.get(self.link)

    def mkdirs(self):
        try:
            os.mkdir('result')
            os.mkdir('result/%s' % (self.search))
        except:
            try:
                os.mkdir('result/%s' % (self.search))
            except:
                print('', end='')

    def scan(self):
        alink = []
        cln = []
        i = 1
        while True:
            html_page = self.alf.page_source
            soup = BeautifulSoup(html_page, 'html.parser')
            elem = soup.find_all('img')

            for k in elem:
                try:
                    if '75x75_RS' in k['src']:
                        k = k['src'].replace('75x75_RS', 'originals')
                    else:
                        k = k['src'].replace('236x', 'originals')

                    named = k.split('/')[-1]
                    print('%s/%s : %s' % (i, self.amount, named))

                    i += 1

                    if k not in alink:
                        alink.append(k)
                        if 'AccessDenied' in req.get(k).text:
                            k = k.replace('jpg', 'png')
                            if 'AccessDenied' in req.get(k).text:
                                k = k.replace('png', 'gif')

                        cln.append(k)

                    if len(cln) >= self.amount:
                        break

                except:
                    print("\nCek Koneksi Anda, Coba Lagi!")
                    self.quit()
                    exit()

            if len(cln) >= self.amount:
                print('\n')
                break
            else:
                self.alf.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.quit()

        return cln

    def save(self, link):
        self.mkdirs()
        logo_saved = False

        for i in tqdm(range(len(link)), desc='Mengunduh', unit_scale=True):
            k = link[i]
            imgs = req.get(k, headers=headers).content

            # Cek apakah gambar dapat diidentifikasi dan tidak berformat GIF
            try:
                image = Image.open(io.BytesIO(imgs))
                if image.mode == 'RGBA':
                    image.save('temp.png')  # Simpan sementara sebagai PNG
                    image = Image.open('temp.png')
                    os.remove('temp.png')  # Hapus sementara

                image.load()
            except Exception as e:
                print("Gambar dengan URL berikut tidak dapat diidentifikasi:", k)
                print("Error:", str(e))
                continue

            # Simpan gambar pertama sebagai "logo.jpg" jika belum tersimpan
            if not logo_saved:
                with open('result/%s/logo.jpg' % (self.search), 'wb+') as p:
                    p.write(imgs)
                    p.close()

                    # Resize gambar menjadi 512x512 piksel
                    new_size_512 = (512, 512)
                    image_resized_512 = self.resize_image('result/%s/logo.jpg' % (self.search), new_size_512)
                    image_resized_512.save('result/%s/logo.jpg' % (self.search), quality=95)

                logo_saved = True
            else:
                # Simpan gambar kedua sebagai "b1024.jpg" jika belum tersimpan
                if i == 1:
                    with open('result/%s/b1024.jpg' % (self.search), 'wb+') as p:
                        p.write(imgs)
                        p.close()

                        # Resize gambar menjadi 1024x500 piksel
                        new_size_1024x500 = (1024, 500)
                        image_resized_1024x500 = self.resize_image('result/%s/b1024.jpg' % (self.search), new_size_1024x500)
                        image_resized_1024x500.save('result/%s/b1024.jpg' % (self.search), quality=95)
                else:
                    # Simpan gambar-gambar lain dengan ukuran asli dan beri nama "ss1.jpg", "ss2.jpg", "ss3.jpg", dan seterusnya
                    rename = k.split('/')[-1]
                    with open('result/%s/ss%s.jpg' % (self.search, i-1), 'wb+') as p:
                        p.write(imgs)
                        p.close()

                        # Resize gambar menjadi 1080x1920 piksel
                        new_size_1080x1920 = (1080, 1920)
                        image_resized_1080x1920 = self.resize_image('result/%s/ss%s.jpg' % (self.search, i-1), new_size_1080x1920)
                        image_resized_1080x1920.save('result/%s/ss%s.jpg' % (self.search, i-1), quality=95)

        print('\n')

    def resize_image(self, image_path, new_size):
        image = Image.open(image_path)
        image_resized = image.resize(new_size)
        return image_resized

    def quit(self):
        self.alf.quit()

def start():
    os.system('cls')
    print()
    print('| [github.com/algatra] - pinterest scraper |'.center(columns, '-'))
    try:
        with open("keywords.txt", 'r') as file:
            keywords = file.read().splitlines()
            amount = int(input("   -> Jumlah : "))
            print('| Memindai . . . |'.center(columns, '-'))
            for keyword in keywords:
                try:
                    run = Pints(keyword, amount)
                    pas = run.scan()
                    print('| Mengunduh . . . |'.center(columns, '-'))
                    run.save(pas)
                except Exception as e:
                    print("Terjadi kesalahan saat mencari gambar untuk keyword:", keyword)
                    print("Error:", str(e))
                finally:
                    print("Pengunduhan untuk keyword '{}' selesai.".format(keyword))
                    print('=' * columns)
    except Exception as e:
        print("Gagal membaca file teks.")

    print('| Selesai ! |'.center(columns, '-'))


if __name__ == '__main__':
    start()
