# CDDA Game Launcher

A [Cataclysm: Dark Days Ahead](https://cataclysmdda.org/) launcher with additional features.

![GitHub Workflow Status (master)](https://img.shields.io/github/workflow/status/DazedNConfused-/CDDA-Game-Launcher/build/master?label=master)
![GitHub Workflow Status (develop)](https://img.shields.io/github/workflow/status/DazedNConfused-/CDDA-Game-Launcher/build/develop?label=develop)

![GitHub release (latest by date)](https://img.shields.io/github/v/release/DazedNConfused-/CDDA-Game-Launcher)
![GitHub all releases](https://img.shields.io/github/downloads/DazedNConfused-/CDDA-Game-Launcher/total)
[![GitHub forks](https://img.shields.io/github/forks/DazedNConfused-/CDDA-Game-Launcher)](https://github.com/DazedNConfused-/CDDA-Game-Launcher/network)

[Download here](https://github.com/DazedNConfused-/CDDA-Game-Launcher/releases).

## ~~Un~~maintained

~~Maintenance and support for this application has now ended. You might still be able to use it but no guarantee is provided. Feel free to fork it, change it, rebuild it or leave it as you please.~~

Maintenance and support for this application has resumed _**in limited capacity**_. Until I learn more about both the launcher codebase _and the game itself_, expect mostly fixes for the bugs I have encountered myself during my CDDA play sessions.

Bug reports and feature requests are still welcome and encouraged, with the tacit understanding that I may not be able to attend them all until I get more seasoned with both game and launcher.

## Implemented features

* Launching the game
* Detecting the game version and build number
* Retreiving the available update builds
* Automatically updating the game while preserving the user modifications
* Soundpack manager
* Mod manager
* Save backups and automatic backups

## ~~Planned features~~

* ~~Tileset manager~~
* ~~Font presets~~

No planed features, only maintenance and bugfixes in the short term. Although having a Tileset manager would indeed be nice, it may be a scope far too ambitious for a project just resurrected from beyond the grave. We shall see.

## FAQ

### What happened to the previous CDDA Game Launcher?

It has become unmaintained. Nevertheless, praise and gratitude go to [remyroy](https://github.com/remyroy) & [the rest of contributors](https://github.com/remyroy/CDDA-Game-Launcher/graphs/contributors) for their work on the launcher thus far, and for giving such a useful tool free of charge to the CDDA community.

### Where is my previous version?

Is it stored in the `previous_version` directory inside your game directory.

### How does the launcher update my game?

* The launcher downloads the archive for the new version.
* If the `previous_version` subdirectory exists, the launcher moves it in the recycle bin.
* The launcher moves everything from the game directory in the `previous_version` subdirectory.
* The launcher extracts the downloaded archive in the game directory.
* The launcher inspect what is in the `previous_version` directory and it copies the saves, the mods, the tilesets, the soundpacks and a bunch of others useful files from the `previous_version` directory that are missing from the downloaded archive to the real game directory. It will assume that mods that are included in the downloaded archive are the newest and latest version and it will keep those by comparing their unique ident value.

### I think the launcher just deleted my files. What can I do?

The launcher goes to great lengths not to delete any file that could be important to you. With the default and recommended settings, the launcher will always move files instead of deleting them. If you think you lost files during an update, check out the `previous_version` subdirectory. That is where you should be able to find your previous game version. You can also check for files in your recycle bin. Those are the main 2 places where files are moved and where you should be able to find them.

### My antivirus product detected the launcher as a threat. What can I do?

Poor antivirus products are known to detect the launcher as a threat and block its execution or delete the launcher. A simple workaround is to add the launcher binary in your antivirus whitelist or select the action to trust this binary when detected.

If you are paranoid, you can always inspect the source code yourself and build the launcher from the source code. You are still likely to get false positives. There is little productive efforts we can do as software developers with these. We have [a nice building guide](https://github.com/DazedNConfused-/CDDA-Game-Launcher/blob/master/BUILDING.md) for those who want to build the launcher from the source code.

Many people are dying to know why antivirus products are identifying the launcher as a threat. There has been many wild speculations to try to pinpoint the root cause for this. The best way to find out would be to ask those antivirus product developers. Unfortunatly, they are unlikely to respond for many good reasons. We could also speculate on this for days on end. Our current best speculation is because we use a component called PyInstaller [that is commonly flagged as a threat](https://github.com/pyinstaller/pyinstaller/issues/4633). Now, if you want see how deep the rabbit hole goes, you can keep on searching or speculating on why PyInstaller itself is commonly flagged as a threat. This research is left as an exercise to the reader.

Many people are also asking why not simply report the launcher as a false positive to those antivirus products. We welcome anyone who wants to take the time to do it, but we believe it is mostly unproductive. Those processes are often time-consuming and ignored. Someone would also have to do them all over again each time we make a new release or when one of the component we use is updated or changed. The current state of threat detection on PC is quite messy and sad especially for everyone using *free* antivirus products.

### I found an issue with the game itself or I would like to make a suggestion for the game itself. What should I do?

You should [contact the game developpers](https://cataclysmdda.org/#ive-found-a-bug--i-would-like-to-make-a-suggestion-what-should-i-do) about this. We are mainly providing a tool to help with the game. We cannot provide support for the game itself.

### How do I update to a new version of the game launcher?

The launcher will automatically check for updated version on start. If it finds one, the launcher will prompt you to update. You can always download [the latest version on github](https://github.com/DazedNConfused-/CDDA-Game-Launcher/releases). Those using the portable version will have to manually download and manually update the launcher. From the help menu, you can also check for new updates.

### The launcher keeps crashing when I start it. What can I do?

You might need to delete your configs file to work around this issue. That filename is `configs.db` and it is located in `%LOCALAPPDATA%\CDDA Game Launcher\`. Some users have reported and encountered unrelated starting issues. In some cases, running a debug version of the launcher to get more logs might help to locate the issue. [Creating an issue about this](https://github.com/DazedNConfused-/CDDA-Game-Launcher/issues) is probably the way to go.

### I just installed the game and it already has a big list of mods. Is there something wrong?

The base game is bundled with a good number of mods. You can view them more like modules that you can activate or ignore when creating a new world in game. These mods or modules can provide a different game experience by adding new items, buildings, mobs, by disabling some game mechanics or by changing how you play the game. They are a simple way of having a distinctive playthrough using the same game engine. The game is quite enjoyable without any of these additional mods or by using the default mods when creating a new world. You should probably avoid using additional mods if you are new to the game for your first playthrough to get familiar with the game mechanics. Once you are comfortable, after one or a few playthroughs, I suggest you check back the base game mods or even some external mods for your next world.

### A mod in the repository is broken or is crashing my game when enabled. What can I do? ###

It is frequent for game updates to break mods especially on the experimental branch. You could try to see if there is an update for that mod. You could try updating that mod by removing it and installing it again. You could try to contact the mod author and ask him to update his mod.

Maintaining external mods can be a difficult task for an ever expanding and changing base game. The only sure and *official* way to have good working mods is to have them included in the base game. If you are concerned about having a reliable gaming experience, you should consider using the base game mods exclusivly and you should consider using the stable branch.

If you find out a mod in the repository is clearly abandonned and not working anymore, please [open an issue](https://github.com/DazedNConfused-/CDDA-Game-Launcher/issues) about it so it can be removed.

### Will you make a Linux or macOS version?

Most likely not. You can check [the linux issue](https://github.com/DazedNConfused-/CDDA-Game-Launcher/issues/329) and [the mac issue](https://github.com/DazedNConfused-/CDDA-Game-Launcher/issues/73) for more information.

### It does not work? Can you help me?

Submit your issues [on Github](https://github.com/DazedNConfused-/CDDA-Game-Launcher/issues). Try to [report bugs effectively](http://www.chiark.greenend.org.uk/~sgtatham/bugs.html).

## Building

You can learn how to run and build the launcher by checking our [building guide](BUILDING.md).

## License

This project is licensed under the terms of [the MIT license](LICENSE).

Permission to use [the launcher icon](cddagl/resources/launcher.ico) was given by [Paul Davey aka Mattahan](http://mattahan.deviantart.com/).

## Contributing to this project

Anyone and everyone is welcome to contribute. Please take a moment to review the [guidelines for contributing](CONTRIBUTING.md).

* [Bug reports](CONTRIBUTING.md#bugs)
* [Feature requests](CONTRIBUTING.md#features)
* [Pull requests](CONTRIBUTING.md#pull-requests)
* [Translation contributions](CONTRIBUTING.md#translations)

## Code of conduct

Participants in this projet are expected to follow [the Code of Conduct](CODE_OF_CONDUCT.md).
