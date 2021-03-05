#! /bin/bash

# mac (sips built-in)
if [ "$(uname)" == "Darwin" ]; then
    find ./docs/assets/headshots -iname "*.png" -type f -exec sh -c 'sips -s format jpeg "$0" --out "${0%.png}.jpeg"' {} \;
    find ./docs/assets/splash -iname "*.png" -type f -exec sh -c 'sips -s format jpeg "$0" --out "${0%.png}.jpeg"' {} \;
    find ./docs/assets/podcasts -iname "*.png" -type f -exec sh -c 'sips -s format jpeg "$0" --out "${0%.png}.jpeg"' {} \;
# linux (imagemagic)
else
    find ./docs/assets/headshots -iname "*.png" -type f -exec sh -c 'convert "$0" -quality 90 "${0%.png}.jpeg"' {} \;
    find ./docs/assets/splash -iname "*.png" -type f -exec sh -c 'convert "$0" -quality 90 "${0%.png}.jpeg"' {} \;
    find ./docs/assets/podcasts -iname "*.png" -type f -exec sh -c 'convert "$0" -quality 90 "${0%.png}.jpeg"' {} \;
fi
