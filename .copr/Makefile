# Create SRPM packages on Fedora Copr using the `make srpm` method
#   https://docs.pagure.org/copr.copr/user_documentation.html#scm

# make -f <cloned_repodir>/.copr/Makefile srpm outdir="<outdir>" spec="<spec_path>"


srpm:
	dnf -y install rpm-build
	rpmbuild -bs $(spec)
	mv /builddir/build/SRPMS/*.rpm $(outdir)
