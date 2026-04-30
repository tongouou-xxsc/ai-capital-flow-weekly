from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_capital_flow.email_delivery import main


if __name__ == "__main__":
    main()
