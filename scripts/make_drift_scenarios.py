from pathlib import Path

import numpy as np
import pandas as pd

TEST_PATH = Path("data/processed/test.csv")
OUT_DIR = Path("data/simulated")
N = 1000
SEED = 42

PATHS = [
    "/about",
    "/docs/getting-started",
    "/search?q=laptop&page=2",
    "/products/12345",
    "/blog/2026/10/how-we-ship",
    "/account/settings",
    "/files/annual-report-2026.pdf",
    "/wiki/Main_Page",
    "/en-us/support/contact",
    "/category/news/page/3",
    "/user/profile?id=42",
    "/login",
]


def main() -> None:
    rng = np.random.default_rng(SEED)
    test = pd.read_csv(TEST_PATH)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    normal = test["url"].sample(n=N, random_state=SEED)
    (OUT_DIR / "normal.txt").write_text("\n".join(normal) + "\n")

    legit = test.loc[test["is_phishing"] == 0, "url"].str.rstrip("/")
    bases = legit.sample(n=N, replace=True, random_state=SEED).tolist()
    picks = rng.integers(0, len(PATHS), N)
    shifted = [base + PATHS[i] for base, i in zip(bases, picks, strict=True)]
    (OUT_DIR / "shifted.txt").write_text("\n".join(shifted) + "\n")

    print(f"Wrote {N} URLs each to {OUT_DIR}/normal.txt and {OUT_DIR}/shifted.txt")


if __name__ == "__main__":
    main()
