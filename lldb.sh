#!/bin/bash

/opt/mongodbtoolchain/v3/bin/lldb mongod \
                                  -o "b src/mongo/db/ftdc/controller.cpp:256" \
                                  -o "run" \
                                  -o "p _mostRecentPeriodicDocument"
