A CA file has been bootstrapped using certificates from the SystemRoots
keychain. To add additional certificates (e.g. the certificates added in
the System keychain), place .pem files in
  /usr/local/etc/openssl/certs

and run
  /usr/local/opt/openssl/bin/c_rehash

openssl is keg-only, which means it was not symlinked into /usr/local,
because Apple has deprecated use of OpenSSL in favor of its own TLS and crypto libraries.

If you need to have openssl first in your PATH run:
  echo 'export PATH="/usr/local/opt/openssl/bin:$PATH"' >> ~/.bash_profile

For compilers to find openssl you may need to set:
  export LDFLAGS="-L/usr/local/opt/openssl/lib"
  export CPPFLAGS="-I/usr/local/opt/openssl/include"

For pkg-config to find openssl you may need to set:
  export PKG_CONFIG_PATH="/usr/local/opt/openssl/lib/pkgconfig"

==> qt
We agreed to the Qt open source license for you.
If this is unacceptable you should uninstall.

qt is keg-only, which means it was not symlinked into /usr/local,
because Qt 5 has CMake issues when linked.

If you need to have qt first in your PATH run:
  echo 'export PATH="/usr/local/opt/qt/bin:$PATH"' >> ~/.bash_profile

For compilers to find qt you may need to set:
  export LDFLAGS="-L/usr/local/opt/qt/lib"
  export CPPFLAGS="-I/usr/local/opt/qt/include"

For pkg-config to find qt you may need to set:
  export PKG_CONFIG_PATH="/usr/local/opt/qt/lib/pkgconfig"

==> sip
The sip-dir for Python is /usr/local/share/sip.