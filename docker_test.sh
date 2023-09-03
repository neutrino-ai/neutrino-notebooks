#!/bin/bash
docker build -t neutrino-cli .
docker run -it neutrino-cli /bin/bash
