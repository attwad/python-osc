# Change Log
All notable changes to this project will be documented in this file.
 
The format is based on [Keep a Changelog](http://keepachangelog.com/) and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

## [1.9.1]

- Reinstate mistakenly deleted package type annotations

## [1.9.0]

- Added TCP Client and Server support for OSC 1.0 and OSC 1.1 formats, with support for sending responses to the client
- Added response support to the existing UDP Client and Server code

## [1.8.3]

- Using trusted publisher setup to publish to pypi

## [1.8.2]

- Changed packaging method to pypa/build
- Removed pygame example to simplify dependencies

## [1.8.1]

- Add options to UdpClient to force the use of IPv4 when IPv6 is available and vice versa

- Add support for arguments with Nil type

### [1.8.0]

- Support for sending and receiving Int64 datatype (`h`).

## [1.7.7]

###  Fixed

Flaky NTP test

## [1.7.6]

### Added

-  Support for python 3.7 and 3.8.

-  Releasing wheel on top of source package.

## [1.7.4]

### Added

- Support for sending nil values.

- IPV6 support to UDPClient.

### Fixed

Timestamp parsing
