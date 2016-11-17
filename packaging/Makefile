
build-deb:
	- mkdir build > /dev/null 2>&1
	- rm build/a.zip > /dev/null 2>&1
	- rm -r build/package > /dev/null 2>&1

	#zipping and then unzipping as a quick hacky way of following symlinks and stripping metadata I think.
	#Forgot exactly why I did it this way.
	zip -r build/a.zip package/

	#Move into the build dir
	cd build

	#unzip, get rid of zip file.
	unzip build/a.zip -d build
	#Cleanup
	pyclean build/package

	rm build/a.zip
	chown -R root build/package
	chmod -R 655 build/package
	chmod -R 755 build/package/DEBIAN
	chmod 755 build/package/opt/scrapbook-note/scrapbook-log.py
	chmod 755 build/package/opt/scrapbook-note/__main__.py
	dpkg-deb -b build/package build
	rm -r build/package
