# Point Playwright at the browsers nixpkgs builds. The ones Playwright
# downloads for itself are not linked for NixOS and will not start.
#
# Usage: source env.sh
export PLAYWRIGHT_BROWSERS_PATH="$(nix build --no-link --print-out-paths nixpkgs#playwright-driver.browsers)"
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
echo "PLAYWRIGHT_BROWSERS_PATH=$PLAYWRIGHT_BROWSERS_PATH"
