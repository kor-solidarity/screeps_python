screeps-starter-python
======================

[![MIT licensed][mit-badge]][mit-url]
[![Slack Chat][slack-badge]][slack-url]
[![Docs Built][docs-badge]][docs-url]

This repository is a starter Python AI written for the JavaScript based MMO
game, [screeps](https://screeps.com).


While code uploaded to the server must be in JavaScript, this repository is
written in Python. We use the [Transcrypt](https://github.com/QQuick/Transcrypt)
transpiler to transpile the python programming into JavaScript.

Specifically, it uses [my fork of
transcrypt](https://github.com/daboross/Transcrypt) built with [a few
modifications](https://github.com/daboross/Transcrypt/commits/screeps-safe-modifications)
intended to reduce the overhead of running Python in the Screeps
environment. Nothing against Transcrypt itself, and you're free to change the
installed fork my modifying `requirements.txt`! I've just found a few changes
useful that I've tested in node.js and the screeps environment, but that I don't
have time to generalize enough to include in the main transcrypt codebase.

This repository is intended as a base to be used for building more complex AIs,
and has all the tooling needed to transpile Python into JavaScript set up.

## Install

To get started, check out the [Setup
Guide](https://daboross.gitbook.io/screeps-starter-python/logistics/setup).

## Docs

For a documentation index, see [The
Book](https://daboross.gitbooks.io/screeps-starter-python/), and for the
main differences between Python and Transcrypt-flavored-Python, see [Syntax
Changes](https://daboross.gitbooks.io/screeps-starter-python/syntax-changes/).

## Community

Join us on the [Screeps Slack][slack-url]! We're in
[#python](https://screeps.slack.com/archives/C2FNJBGH0) (though you need to sign
up with the first link first :).

[mit-badge]: https://img.shields.io/badge/license-MIT-blue.svg
[mit-url]: https://github.com/daboross/screeps-starter-python/blob/master/LICENSE
[slack-badge]: https://img.shields.io/badge/chat-slack-2EB67D
[slack-url]: https://chat.screeps.com/

[docs-badge]: https://img.shields.io/badge/docs-built-blue
[docs-url]: https://daboross.gitbook.io/screeps-starter-python/logistics/setup
