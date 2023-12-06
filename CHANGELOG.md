## 0.7
* Added network features
* Added ability to update cart in-place from official cart website without losing saves or custom games
* Fix bootloader size issue in sketch backup
* Fix bug on very few games where large blocks of white pixels in data would be trimmed

## 0.6.1
* Fixed weird C++ object deleted bug
* Fixed inability to open cart builder by itself anymore
* Image saving remembers last spot

## 0.6.0

* Updated arduboy package import and creator to support the proper "v3" format
* Updated arduboy package editor to be significantly more robust
* Support licensing for arduboy packages
* Arduboy package exports use new, backwards compatible "v4" format (see bottom of post)
* Moved elements around on main gui for hopefully a more logical flow
* Added last performed action to bottom of main gui
* Clicking on last performed action opens a debug window with all actions performed this session
* Added FAQ section (feel free to suggest more for this)
* Updated help with more links to external tools and information on Arduboy
* Added lots of unit tests

Please see https://community.arduboy.com/t/arduboy-toolset/11227/161 for information on updated arduboy package format


## 0.5.0

* Added visual alert when info section will get cut off in cart builder (thank you @steka)
* Added image converter
* Added contrast patch options to fx and sketch upload (thank you Mr.Blinky)
* Decommissioned CLI app (will make another one later)

## 0.4.1

* Added more fields to arduboy package creator (including auto-set hidden date)
* Removed button to cart builder, renamed Utilities tab to Package
* Updated cart builder help with links to where to find games
* Updated "about" with more information + used packages, added "about" Cart Editor

## 0.4.0

* Fixed major bug where setting program actually sets fx data (sorry!!)
* Added silly + simple .arduboy package creator to toolset (for now it's a duplicate of the slot widget, may have more fields later)
* Added ability to tack on FX dev data on sketch upload
* Detect when FX data has save at the end, alert + ask if you want to split
* Stop logging every time arduboy is pinged from main app (fills logs with useless junk)
* Make arduboy parser prefer an image called "title.png" if available (for title)

## 0.3.1

Small changes, export to .arduboy

* Moved cart builder menu options around
* Can export individual slots or the entire cart to .arduboy files
* Windows + MacOS use python 3.8 now (a downgrade to increase support maybe?)
* Single Mac release for now, just intel
* Multi-drag-and-drop (each file treated as a separate slot!)
* Added more to cart builder help

## 0.3

Support MacOS + Small comfort changes

* Made categories way more obvious
* Can jump up and down through categories with the menu or keyboard shortcuts
* Can shift slots up and down with a keyboard shortcut (see in Cart menu)
* Visual indication that a game is FX enabled
* Ability to clear FX data or FX save if accidentally added (Debug menu)
* Increased "info" input limit from 150 to 175.

## 0.2.2

Major bugfix

* Fixed 'next page' header issue (0.2 - 0.2.1 do not work)

## 0.2.1

Small feature update

* Move whole categories up/down, or delete them
* Auto-generated images show up in UI if cart compiled without them (was already auto-generating them)
* Ability to add 4k chunks to a save section without opening a file
* Parse more data more appropriately from .arduboy files

## 0.2

Added cart builder

* File menu + exit from file menu
* Added drag + drop for all file selectors
* Added cart builder
  * Load flashcart directly off arduboy into editor
  * Add/remove/rearrange games + categories
  * Drag + drop .hex + .arduboy files
  * Flash back to arduboy when done, or save backup

## 0.1

Initial release

* Sketch upload / backup (to bin)
* FX flash upload / backup (to bin)
* EEPROM upload / backup / erase
* GUI + CLI program packaged into release for windows + linux
* Help + about in GUI
* Run ops on multiple arduboys (CLI only, untested)