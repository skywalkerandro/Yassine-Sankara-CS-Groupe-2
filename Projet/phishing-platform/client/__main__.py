"""Point d'entree du client (permet : python -m client  et le build PyInstaller)."""
import sys
from pathlib import Path

# Garantit que la racine du projet est dans le path (utile pour PyInstaller).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from client.app import main

if __name__ == "__main__":
    sys.exit(main())
