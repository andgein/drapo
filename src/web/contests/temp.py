#!/usr/bin/env python3

import os
import time

from bs4 import BeautifulSoup as bs
import requests


USERS_FILE_LOCATION = 'users.txt'
DELAY_SECONDS = 0.5
ADDRESS = os.environ.get('TASK_ADDRESS', 'http://3ch.ructf.org')
PICTURES = [
    'https://lh6.ggpht.com/2J4ThT6bsPajr3LjwU4D4UyJ2DE45gIVIpNWf2OXRJL063NAarb_YVKv3DrXg3H-dCZe=w300',
    'https://lh5.ggpht.com/hehxa9VHtYJxBsQT8LTIJjoroJnkmEQ6ZAvmtwW1tiaKOaBu-4ZSyVqptoZ_Syr63hc=w170',
    'http://i.imgur.com/3Kf5e.png',
    'https://img.memesuper.com/23bb7ebb85e67aa3b3122ef8cd969585_rage-comics-teh-meme-wiki-meme-character-faces_997-1030.png',
    'https://s-media-cache-ak0.pinimg.com/736x/d2/ee/2f/d2ee2f5f24bc2029339d59c9657fa213--harp-rage-faces.jpg',
    'http://www.ozpolitic.com/album/forum-attachments/request_large_rage_comic_faces_for__1877054656_640x0.jpg',
    'http://static4.fjcdn.com/thumbnails/comments/Oh+god+a+second+carlos+_52acbdea172cb566897d184f98fefa68.png',
    'http://i1.kym-cdn.com/entries/icons/original/000/004/077/Raisins_Face.jpg',
    'https://s-media-cache-ak0.pinimg.com/originals/9e/28/c4/9e28c4f84d5e48ca6ab46b08115333b2--forever-alone-meme-rage-faces.jpg',
    'https://s-media-cache-ak0.pinimg.com/736x/61/f0/60/61f0603ccfaf235b0ef728fe5ec3cb35--faces-to-draw-meme-rage-comics.jpg',
    'http://dendaienglish.wikispaces.com/file/view/43.png/265363266/231x184/43.png',
    'https://s-media-cache-ak0.pinimg.com/564x/7f/36/11/7f3611d60c269f57831de3441cae21fa.jpg',
    'https://s-media-cache-ak0.pinimg.com/originals/c2/f9/1f/c2f91f24e49e9dae02057d36cf2ec0ce.jpg',
    'https://fthmb.tqn.com/xuBxdoco3vpAZ60nkZc72xcPq6w=/768x0/filters:no_upscale()/about/lolguy-58072dbe5f9b5805c2396cfd.png',
    'https://s-media-cache-ak0.pinimg.com/736x/d6/57/d5/d657d5cd403f64311fe8a7380f905e1d--meme-rage-comics-sad-faces.jpg',
]


current_picture = 0


class User:
    def __init__(self, username, passwd, motto):
        self.username = username
        self.passwds = [ passwd ]
        self.images = []
        self.motto = motto


def load_users(users_file):
    result = []
    with open(users_file, 'rt') as f:
        lines = f.readlines()
    for line in lines:
        username, passwd, motto = line.strip().split(':')
        result.append(User(username, passwd, motto))
    return result


if __name__ == "__main__":
    users = [ user for user in load_users(USERS_FILE_LOCATION) if user.username.startswith('m00t_') ]

    while True:
        pic = PICTURES[current_picture]
        current_picture = (current_picture + 1) % len(PICTURES)

        for user in users:
            print(user.username)
            s = requests.Session()
            response = s.get(ADDRESS + '/signin', query={'username' : user.username,
                                                  'passwd' : user.passwds[0]})

            if response.status_code != requests.codes.ok:
                print("Failed to login into user %s: server returned status %d" % (user.username, response.status_code))
                continue

            soup = bs(response.text, "lxml")
            for image in soup.findAll("img"):
                s.get(image["src"])


            response = s.get(ADDRESS + '/addimg', query={'src' : pic})
            if response.status_code != requests.codes.ok:
                print("Failed to add image: server returned status %d" % response.status_code)
                continue

            time.sleep(DELAY_SECONDS)