mkdir build > /dev/null
rm build/a.zip >/dev/null
rm -r build/package>/dev/null
zip -r build/a.zip package/
cd build
pyclean .
unzip a.zip
rm a.zip
chown -R root package
chmod 755 package/opt/scrapbook-note/__main__.py
dpkg-deb -b package .
rm -r package
