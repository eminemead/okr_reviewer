#!/bin/bash

echo "=== Helix Installation Diagnostic ==="
echo ""

# Check if helix is installed via brew
if command -v brew &> /dev/null; then
    echo "✓ Homebrew is installed"
    BREW_PREFIX=$(brew --prefix)
    echo "Brew prefix: $BREW_PREFIX"
    
    # Check if helix is installed
    if brew list helix &> /dev/null; then
        echo "✓ Helix is installed via brew"
        
        # Check helix binary location
        HELIX_PATH="$BREW_PREFIX/bin/helix"
        if [ -f "$HELIX_PATH" ]; then
            echo "✓ Helix binary found at: $HELIX_PATH"
            
            # Check if it's in PATH
            if echo "$PATH" | grep -q "$BREW_PREFIX/bin"; then
                echo "✓ Brew bin directory is in PATH"
            else
                echo "✗ Brew bin directory NOT in PATH"
                echo ""
                echo "=== SOLUTION ==="
                echo "Add this to your shell config file:"
                echo ""
                echo 'export PATH="'$BREW_PREFIX'/bin:$PATH"'
                echo ""
                echo "Then run: source ~/.bashrc (or ~/.zshrc)"
            fi
        else
            echo "✗ Helix binary not found at expected location"
        fi
    else
        echo "✗ Helix is not installed via brew"
        echo "Run: brew install helix"
    fi
else
    echo "✗ Homebrew is not installed"
    echo "Install it first: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
fi

echo ""
echo "=== Current PATH ==="
echo "$PATH"
