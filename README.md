# sensebook
Making sense of Facebooks undocumented API.

[![License](https://img.shields.io/pypi/l/sensebook.svg)](https://github.com/madsmtm/sensebook/blob/master/LICENSE.txt)
![Supported Python Versions](https://img.shields.io/pypi/pyversions/sensebook.svg)
![Implementations](https://img.shields.io/pypi/implementation/sensebook.svg)
![Project Status](https://img.shields.io/pypi/status/sensebook.svg)
[![Version](https://img.shields.io/pypi/v/sensebook.svg)](https://pypi.org/project/sensebook/)
[![Build Status](https://travis-ci.com/madsmtm/sensebook.svg)](https://travis-ci.com/madsmtm/sensebook)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

This project attempts to document Facebooks undocumented API, so that libraries can
interact with Facebook in the same way the browser does. The main focus is Facebooks
Messenger, and enabling users to send, recieve and fetch messages.

The primary focus is Python, but the code should be readable enough that it can be
translated to other languages.

The goal is neither to make an asyncronous nor syncronous implementation, but to make a
[Sans-IO](https://sans-io.readthedocs.io/) framework where up such a thing can be built.
Hence, the project won't be very useful on it's own. If you just want a plug n' play
library, see [fbchat](https://github.com/carpedm20/fbchat).

Note: This project is not affiliated with Facebook, Inc. or any of that stuff,
and I'll have to comply if I recieve a takedown notice.


## Installation
```sh
pip install sensebook
```


## License
BSD 3-Clause, see `LICENSE.txt`.


## Code of Conduct
This project follows the Contributor Covenant Code of Conduct, see
`CODE_OF_CONDUCT.txt`. Note, however, that I'm far from an expert in this area,
so feel free to reach out to me if I've offended anybody or made a mistake.
Open Source should be for everyone!
