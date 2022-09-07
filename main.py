# Nam Nguyen
# Sep 7, 2022
# Discord Bot that prints out pictures as custom emojis through the command ::printPic

import numpy as np
from PIL import Image
import discord
import math
from discord.ext import commands
import requests
import shutil
import uuid
import os

# Token of the discord bot
TOKEN = ''

# Discord Group ID
guildID = 0

# Map correlating the discord group's custom discord emojis to their avg RGB value
emoMap = {}

intents = discord.Intents.default()
intents.members = True
client = commands.Bot(intents=intents, command_prefix='::')


# Pre:
#   arr: Takes in array of RGB values
#
# Post:
#   Returns the average RGB values of the given array
def avgRGB(arr):
    red = 0
    green = 0
    blue = 0
    for i in np.arange(0, len(arr)):
        for j in np.arange(0, len(arr[0])):
            red += arr[i][j][0]
            green += arr[i][j][1]
            blue += arr[i][j][2]
    return [red/(len(arr)*len(arr[0])), green/(len(arr)*len(arr[0])), blue/(len(arr)*len(arr[0]))]


# Pre:
#   emoji: Takes in an emoji object
#
# Post:
#   Returns the avg RGB values of the emoji
def returnEmoRGB(emoji):
    arrRGB = []
    url = emoji.url
    r = requests.get(url, stream=True)
    imageName = emoji.name + '.png'
    with open(imageName, 'wb') as out_file:
        shutil.copyfileobj(r.raw, out_file)
        img = Image.open(out_file.name)
        arrRGB = avgRGB(np.array(img))
    os.remove(imageName)
    return arrRGB


# Post:
#   When the bot is started, it calculates and stores the average RGB values of the custom emojis in emoMap
@client.event
async def on_ready():
    global emoMap
    for emoji in client.get_guild(guildID).emojis:
        try:
            emoMap["<:" + emoji.name + ":" + str(emoji.id) + ">"] = returnEmoRGB(emoji)
        except Image.UnidentifiedImageError:
            os.remove(emoji.name + '.png')
            pass
    print(emoMap)


# Post:
#   Processes commands if the commands aren't coming from the bot itself.
@client.event
async def on_message(message):
    if (message.author != client.user):
        await client.process_commands(message)


# Pixel object represents the section of the full picture that we are going to represent with a single emoji. By taking
# in a specific array of RGB values of a specific section of the picture, the class finds the best emoji to represent
# the section.
class Pixel:

    # Pre:
    #   emoji_set: The map of emojis connected to RGB values
    #   arr: array of RGB values of the section
    #
    # Post:
    #   Constructs a Pixel object
    def __init__(self, emoji_set, arr):
        self.arr = arr
        self.emoji_set = emoji_set

    # Post:
    #   Returns the emoji that best fits with the section colorwise
    def symbol(self):
        avgPixRGB = avgRGB(self.arr)
        symbol = ''
        lowestRGBdiff = 442
        for key in self.emoji_set.keys():
            if lowestRGBdiff > math.sqrt(math.pow(self.emoji_set[key][0] - avgPixRGB[0], 2) + math.pow(self.emoji_set[key][1] - avgPixRGB[1], 2) + math.pow(self.emoji_set[key][2] - avgPixRGB[2], 2)):
                symbol = key
                lowestRGBdiff = math.sqrt(math.pow(self.emoji_set[key][0] - avgPixRGB[0], 2) + math.pow(self.emoji_set[key][1] - avgPixRGB[1], 2) + math.pow(self.emoji_set[key][2] - avgPixRGB[2], 2))
        return symbol


# Pic object represents the entire picture given by the user. By taking in the address of the photo given and the
# map of emojis it can print out pictures in the form of emojis
class Pic:

    # Pre:
    #   emoji_set: The map of emojis connected to RGB values
    #   address: address of the photo given
    #
    # Post:
    #   Constructs a Pic object
    def __init__(self, emoji_set, address, ctx):
        self.emoji_set = emoji_set
        self.address = address
        self.ctx = ctx

    # Pre:
    #   length: The width of the emoji picture printed. length = 5 -> width is 5 emojis
    #
    # Post:
    #   Prints the emoji version of the picture
    async def print_emo_vers(self, length):
        img = Image.open(self.address)
        height = img.height
        width = img.width
        img_matrix = np.array(img)
        print(img_matrix)
        for i in np.arange(0, height - math.floor(width/length), math.floor(width/length)):
            text_pic = ""
            for j in np.arange(0, width - math.floor(width/length), math.floor(width/length)):
                pix = Pixel(self.emoji_set, img_matrix[i:(i + math.floor(width/length)), j:(j + math.floor(width/length))])
                text_pic += pix.symbol()
            await self.ctx.send(text_pic)


# Pre:
#   width: The width of the emoji picture printed. width = 5 -> width is 5 emojis
#
# Post:
#   Entering the command ::printPic 5 along with an uploaded photo in the thread which
#   the bot can see will result in the bot printing pic with just emojis.
@client.command()
async def printPic(ctx, width):
    try:
        url = ctx.message.attachments[0].url
    except IndexError:
        print("Error: No attachments")
        await ctx.send("No attachments detected BITCH!")
    else:
        if url[0:26] == "https:#cdn.discordapp.com":
            r = requests.get(url, stream=True)
            imageName = str(uuid.uuid4()) + '.jpg'
            with open(imageName, 'wb') as out_file:
                shutil.copyfileobj(r.raw, out_file)
                pic = Pic(emoMap, out_file.name, ctx)
                await pic.print_emo_vers(width)
            os.remove(imageName)


client.run(TOKEN)
