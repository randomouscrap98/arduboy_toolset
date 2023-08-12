## 0.2.3

Small comfort changes

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