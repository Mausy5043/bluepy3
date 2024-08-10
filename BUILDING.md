# BUILDING (the pypi package)

## Versionnumbers

We try to follow [semantic versioning](semver.org).
-  We don't have `0` MINOR or PATCH versionnumbers. Patterns `x.0.z` and `x.y.0` do not exist.
-  Testing versions are identified by odd-numbered MINOR versions.
-  Stable/production versions are identified by even-numbered MINOR versions.
-  MAJOR versions increase only when significant changes are made.

## Building the package for testing

To test changes the package may be built and uploaded to [test.pypi.org](test.pypi.org)
Preferably changes are done on a separate branch.

1.  Make the necessary changes against the `devel` branch
2.  In `./pyproject.toml` change the versionnumber.
    -  For testing we change the MINOR version to the next **odd** value.
    -  The first PATCH version always starts on x.y.1 and increases by +1 with every new build.
    -  Builds with the same versionnumber can't be uploaded to PyPi, so it's not like we have a choice.
3.  Run `./mkbld -b`
4.  Run `./mkbld -t`  *(installation instructions are displayed on the terminal after the upload)*
5.  Test the changes by installing the test package on a computer near you. *NOTE: You may have to try twice or wait a couple of minutes for the download to become available from PyPi.*
6.  Rinse and repeat...
7.  Execute `git commit -a; git push` to commit the changes.
8.  After succesfull testing create a pull request to merge the changes into the `latest` branch.

## Building the package for distribution

To distribute a new production version the package must be built and uploaded to [pypi.org](pypi.org)

1.  Make the necessary changes...
    -  Merges (via PR) from a separate branch are considered MINOR changes.
    -  Fixes etc. may be committed directly to the `latest` branch as a new PATCH version.
2.  In `./pyproject.toml` change the versionnumber.
    -  For merges we change the MINOR version to the next **even** value.
    -  The first PATCH version always starts on x.y.1 and increases by +1 with every new build.
    -  Builds with the same versionnumber can't be uploaded to PyPi, so it's not like we have a choice.
3.  Run `./mkbld -b`
4.  Run `./mkbld -d`  *(installation instructions are displayed on the terminal after the upload)*
5.  Test the changes by installing the distribution package on a computer near you. *NOTE: You may have to try twice or wait a couple of minutes for the download to become available from PyPi.*
6.  Rinse and repeat...
7.  Execute `git commit -a; git push` to commit the changes.
8.  After succesfull testing of the distribution package create a new tag and release on the `latest` branch.

## Support for a (new) version of BlueZ

By default versions 5.47, 5.50, 5.60, 5.66, 5.68, 5.70 of the BlueZ stack are supported. To add support for a new version of the stack and compile the `bluepy3-helper.c` against it the following must be changed:

1.  Create a new branch for testing as detailed above.
2.  Create a copy of the `./bluepy3/config.<version>.h`; where *\<version\>* is the version tagname of the [bluez stack](https://github.com/bluez/bluez) to be used.
    -  In this new file change the `#define`s to match the versionnumber
        ```
        /* Define to the full name and version of this package. */
        #define PACKAGE_STRING "bluez 5.68"
        ...
        /* Define to the version of this package. */
        #define PACKAGE_VERSION "5.68"
        ...
        /* Version number of package */
        #define VERSION "5.68"
        ```
3.  Complete the building instructions for testing as described above.
4.  Install on the test system and use `helpermaker --build <version>` to confirm that it will compile. NOTE: Do NOT use `make` directly.
5.  Make adjustments as needed to get the new version to compile.
