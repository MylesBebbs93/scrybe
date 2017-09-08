#!/usr/bin/env python
import sqlite3 as sql
import os
import hashlib

def createDatabase(path):
    if(not os.path.exists(path)):
        conn = sql.connect(path)
        c = conn.cursor()
        command = "CREATE TABLE notes (id INTEGER PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL, createTime REAL NOT NULL, archived INTEGER NOT NULL, tags TEXT NOT NULL)" #NOTE consider using some ORM solution
        c.execute(command)
        conn.commit()
        conn.close()

def configure(dbPath):
    """
    Perform initial configuration
    Includes setting up an alias for the program and replacing relative paths with absolute ones
    """

    #add needed shell file extensions to list
    shellFiles = [".zshrc", ".bashrc"]

# Following loop assumes that user will have Bash as shell if no configuration
# files were found
    userShellFile = ".bashrc"
    for fileName in shellFiles:
        if(os.path.exists(os.path.join(os.environ["HOME"], fileName))):
                userShellFile = fileName
                break

    cwd = os.getcwd()
    with open(os.path.join(os.environ["HOME"], fileName), 'a+') as rcFile:
        rcFile.write("alias scrybe='python {0}'\n".format(os.path.join(cwd, "scrybe.py")))

    with open(os.path.join(cwd,"dbLib.py"), "r") as oldDbLib:
        newDbLibString = oldDbLib.read().replace("scrybe.db", dbPath)

    with open(os.path.join(cwd, "dbLib.py"), "w") as newDbLib:
        newDbLib.write(newDbLibString)
        newDbLib.close()

    if(not os.path.exists(os.path.join(cwd, ".scrybe.conf"))):
        editor = ""
        while(editor not in ["vim", "emacs", "nano"]):
            editor = raw_input("Vim, emacs or nano?: ").strip().lower()
        with open(os.path.join(cwd, ".scrybe.conf"), "a") as configFile:
            configFile.write("editor:" + editor + "\n")

    with open(os.path.join(cwd, "userLib.py"), "r") as userLib:
        userLibString = userLib.read().replace(".scrybe.conf", os.path.join(cwd, ".scrybe.conf"))
    with open(os.path.join(cwd, "userLib.py"), "w") as userLib:
        userLib.write(userLibString)

def encryptDatabase(dbPath):
    """
    Encryption of the database
    """

    cwd = os.getcwd()
    try:
        from Crypto.Cipher import AES#NOTE - Minimum viable library check
        from Crypto import Random
    except:
        print("Database encryption relies on the pyCrypto library")
        print("To install it run 'sudo pip install pycrypto'")
        install = raw_input("Do that now? (requires pip)(y/n): ").strip().lower()
        if(install == "y"):#NOTE - Assumes user has pip installed - rethink
            os.system("sudo pip install pycrypto")
        else:
            print("Continuing without database encryption")
            return
    print("Enter a passphrase, and keep it somewhere safe")
    print("Your notes CANNOT be retrieved if you lose it")
    userpass1 = ""
    userpass2 = ""
    while(userpass1 != userpass2 or len(userpass1) <= 4):
        userpass1 = raw_input("Passphrase: ")
        userpass2 = raw_input("Repeat passphrase: ")
        if(userpass1 != userpass2):
            print("Sorry, those passwords don't match")
            print("Please try again, or hit control-c")
            print("to finish setup without database encryption")
    userPass = hasher(userpass1)
    iv = Random.new().read(16)
    with open(dbPath, "rb") as plainFile:
        plainText = iv + plainFile.read()#NOTE - iv used to verify decrypt
    while(len(plainText) % 16 != 0):
        plainText += " "
    dbBakPath = os.path.join(cwd, "scrybe.db.bak")
    os.rename(dbPath, dbBakPath)
    encrypter = AES.new(userPass, AES.MODE_CBC, iv)
    with open(os.path.join(cwd, "scrybe.db.enc"), "wb") as encFile:
        encFile.write(iv + encrypter.encrypt(plainText))#iv prepended to ciphertext
    os.remove(dbBakPath)#NOTE - only remove backup after write
    with open(cwd + ".scrybe.conf", "a") as configFile:
        configFile.write("encrypted:true\n")

def hasher(plain):
    i = 0
    while(i < 64000):
        plain = hashlib.sha256(plain).digest()
        i += 1
    return(plain)


def main():
    cwd = os.getcwd()
    #make database if it isn't present
    dbPath = os.path.join(cwd, "scrybe.db")
    createDatabase(dbPath)
    configure(dbPath)

    crypto = raw_input("Encrypt note database at rest(y/n)?: ").strip().lower()
    if(crypto == "y"):
        encryptDatabase(dbPath)


if(__name__ == "__main__"):
    main()
