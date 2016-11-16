Pyandoc: a simple Pandoc wrapper for Python
===========================================

Pyandoc is a simple Python wrapper for the excellent
``pandoc <http://pandoc.org>`` \_\_ utility. It allows you to convert
the format of text documents by interacting with a Document object's
attributes. Each supported format is available as a property, and can
either read from or written to.

Requirements
------------

-  Pandoc

Usage
-----

Get setup.

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. code:: python

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

::

    ::

::

    ::

    import pandoc

.. raw:: html

   </div>

Let's start with a Markdown document:

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. raw:: html

   <div class="sourceCode">

.. code:: python

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

.. raw:: html

   </div>

::

    ::

::

    ::

    doc = pandoc.Document() doc.markdown = ''' # I am an H1 Tag

    -  bullet point
    -  more points

    \* point with [link](http://kennethreitz.com)! '''

.. raw:: html

   </div>

Now let's convert that into a ReST document: :

::

    ::

::

    ::

    ::

        >>> print doc.rst

    **I am an H1 Tag**

    -  bullet point
    -  more points
    -  point with `link <http://kennethreitz.com>`__!

Formats available: - asciidoc - beamer - commonmark - context - docbook
- doc- x - dokuwiki - dzslides - epub - epub3 - fb2 - haddock - html
-html5 - icml - json (pandoc's AST) - latex - man - markdown
-markdown\_github - markdown\_mmd - markdown\_phpextra -markdown\_strict
- mediawiki - native - odt - opendocument - opml - org - pdf - plain
-revealjs - rst - rtf - s5, - slideous - slidy - texinfo -textile

Enjoy.
