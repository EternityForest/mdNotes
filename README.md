mdNotes: Simple Markdown Notetaking
===================================

mdNotes is a WYSYWIG markdown editor written in pyqt5 for python3. Unlike some other md editors, mdNotes does not require extra metadata in md files, and uses the filesystem hierarchy itself for storing notes, for maximum compatibility wiht other tools, especially android phones when using folder sync systems.

mdNotes is not even currently alpha quality yet.

mdNotes internally uses pandoc to load and save markdown and so can be modified easily to support almost any format. However, one should back up any notes before opening them with mdnotes, as it may wreck any fancy formating in the load/save process.

Because mdNotes is designed for notetaking and not programming, it will automatically save all open notes when you close the program or close a tab.

mdNotes also has limited support for reStructuredText files.

Although mdNotes is primarily hierarchal, links to local files are fully supported. mdNotes uses webkit for rendering, so you can freely drag and drop images into pages(images from websites will automatically be downloaded into a local folder in the same directory as the note.

Installation
------------

mdNotes depends on python3, pyqt5, pyqt5 webkit, and send2trash. mdNotes also depends on pyandoc which is included,
but needs to have pandoc installed to work.

On Ubuntu:

```
sudo apt-get install python3-pyqt5 python3-pyqt5.qtwebkit
sudo pip3 install send2trash
```

then simply run `__main__.py`

mdNotes expects either for it's first command line argument to be a path to the notebook folder you want to edit, or for there to be a file at ~/.mdnotes/notebooks.txt that contains the path of the folder you want to be your notes folder.

WARNING
-------
Don't use this in folders containing important notes. This is pre-alpha software.

Theming and customization
------------------------

Because mdNotes renders with webkit, you can put a style.css folder in your notes folder that will be applied to the text. You have to restart mdNotes for a new theme to work.

You can also put a global theme in  ~/.mdnotes/style.css, however themes directly in the notebook will take precedence.
