VERSION=1.0
UBUNTU_VERSION=${VERSION}-0extras13.10.1
PACKAGE_NAME=unity3d-configurator
UBUNTU_PACKAGE_DIR=${PACKAGE_NAME}
UBUNTU_ARCH=$(shell dpkg-architecture -qDEB_HOST_ARCH)

default:
	@echo "There is no build. Please, use (sudo) make install, (sudo) make uninstall, make ubuntu-source or make ubuntu-package"

install: icon.png unity3d-configurator.desktop unity-configurator.py
	@echo "=> Installing..."
	mkdir -p /usr/share/icons
	mkdir -p /usr/share/applications
	mkdir -p /usr/lib/unity3d-configurator
	cp icon.png /usr/share/icons/unity3d-configurator.png
	cp unity3d-configurator.desktop /usr/share/applications
	cp unity-configurator.py /usr/lib/unity3d-configurator/

uninstall:
	@echo "=> Uninstalling..."
	rm /usr/share/icons/unity3d-configurator.png
	rm /usr/share/applications/unity3d-configurator.desktop
	rm /usr/lib/unity3d-configurator/unity-configurator.py

clean: clean-after-debuild
	rm -fR ${UBUNTU_PACKAGE_DIR}/
	rm -f extras-${PACKAGE_NAME}.desktop
	rm -f ${PACKAGE_NAME}_${VERSION}.orig.tar.gz
	rm -f ${PACKAGE_NAME}_${UBUNTU_VERSION}.debian.tar.gz
	rm -f ${PACKAGE_NAME}_${UBUNTU_VERSION}_${UBUNTU_ARCH}.deb
	rm -f ${PACKAGE_NAME}.ubuntu.source.tar.gz

clean-after-debuild:
	rm -f ${PACKAGE_NAME}_${UBUNTU_VERSION}.dsc
	rm -f ${PACKAGE_NAME}_${UBUNTU_VERSION}_${UBUNTU_ARCH}.build
	rm -f ${PACKAGE_NAME}_${UBUNTU_VERSION}_${UBUNTU_ARCH}.changes

ubuntu-package: ${PACKAGE_NAME}_${UBUNTU_VERSION}_${UBUNTU_ARCH}.deb clean-after-debuild

ubuntu-source: orig debian
	@echo "=> Generating ubuntu source package in ${UBUNTU_PACKAGE_DIR}"
	mkdir -p ${UBUNTU_PACKAGE_DIR}/
	cd ${UBUNTU_PACKAGE_DIR}/ ; tar xf ../${PACKAGE_NAME}_${VERSION}.orig.tar.gz --strip=1
	cd ${UBUNTU_PACKAGE_DIR}/ ; tar xf ../${PACKAGE_NAME}_${UBUNTU_VERSION}.debian.tar.gz

ubuntu-submission: ${PACKAGE_NAME}.ubuntu.source.tar.gz clean-after-debuild	

extras-${PACKAGE_NAME}.desktop: unity3d-configurator.desktop
	echo "=> Generating Ubuntu desktop file"
	cat $? \
	| sed 's/\/usr\/lib\/unity3d-configurator\//\/opt\/extras.ubuntu.com\/unity3d-configurator\//' \
	| sed 's/\/usr\/share\/icons\//\/opt\/extras.ubuntu.com\/unity3d-configurator\//' \
	| sed 's/unity3d-configurator\.png/icon.png/' \
	>$@

orig:   ${PACKAGE_NAME}_${VERSION}.orig.tar.gz
debian: ${PACKAGE_NAME}_${UBUNTU_VERSION}.debian.tar.gz

${PACKAGE_NAME}_${VERSION}.orig.tar.gz: icon.png extras-${PACKAGE_NAME}.desktop unity-configurator.py
	echo "=> Generating orig file " $@
	tar czf $@ $? --xform=s,'.*',${PACKAGE_NAME}_${VERSION}/\\0,

${PACKAGE_NAME}_${UBUNTU_VERSION}.debian.tar.gz: debian/*
	echo "=> Generating debian.tar.gz file " $@
	tar czf $@ $?

${PACKAGE_NAME}.ubuntu.source.tar.gz: ${PACKAGE_NAME}_${UBUNTU_VERSION}_${UBUNTU_ARCH}.deb
	echo "=> Generating ubuntu source package " $@
	tar czf $@ \
		${PACKAGE_NAME}_${VERSION}.orig.tar.gz \
		${PACKAGE_NAME}_${UBUNTU_VERSION}.debian.tar.gz \
		${PACKAGE_NAME}_${UBUNTU_VERSION}.dsc

${PACKAGE_NAME}_${UBUNTU_VERSION}_${UBUNTU_ARCH}.deb: ubuntu-source
	echo "=> Building ubuntu package " $@
	cd ${UBUNTU_PACKAGE_DIR}/debian ; debuild
	
