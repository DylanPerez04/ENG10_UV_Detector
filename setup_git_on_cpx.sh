echo "INSTURCTIONS:
Run this script in your WSL (Windows Subsystem for Linux) Ubuntu
shell in the home directory while your Circuit Playground Express (cpx) is connected to your computer via USB.
"

folder = "cpx_drive"

read -p "Enter drive letter: " letter

sudo cd ~
sudo mkdir -p ~/mnt/$folder/
sudo mount -t drvfs D: /mnt/$folder/
mkdir -p ~/circuitpy-git 
git --git-dir=$HOME/circuitpy-git --work-tree=/mnt/$folder init
echo 'alias cpgit="git --git-dir=$HOME/circuitpy-git --work-tree=/mnt/d"' >> ~/.bashrc 
source ~/.bashrc
cpgit remote add origin https://github.com/DylanPerez04/ENG10_UV_Detector.git

echo "Now, in your home directory or in /mnt/$folder/, you can run cpgit add ., cpgit commit -m, and cpgit push origin master, etc"

echo "To push from your shell to github, you need to connect your github account to your shell. Do this with:
 $ ssh-keygen -t rsa -b 4096 -C github_email

You are about to generate a public key and a secret private key called ~/.ssh/id_rsa on your computer. If anyone gets ahold of that file they can SSH into all of the things you can SSH into, so you want to protect that file. One way you can protect it is to add a passphrase which is the next prompt it will give you. Press Enter twice to continue without setting a passphrase. Though if you really want to set a passphrase, refer to GitHub docs on passphrases.

By default, the public SSH key is saved to a file at ~/.ssh/id_rsa.pub.

View the contents of ~/.ssh/id_rsa.pub (using cat), then copy the contents of the public key file to your clipboard.
"
