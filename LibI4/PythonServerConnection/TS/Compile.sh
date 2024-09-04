#!/bin/bash

echo "Creating dir..."
mkdir ./Compiled

echo "Deleting old files..."
rm ./Compiled/*.js

echo "Compiling new files..."
npx tsc ./*.ts --outDir ./Compiled/ --strict --forceConsistentCasingInFileNames --esModuleInterop --downlevelIteration --target es6 --module es6 --moduleResolution node