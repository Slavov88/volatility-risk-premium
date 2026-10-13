import argparse
from vrp.quant_portfolio import acquire_spy, run_h8
from vrp.quant_extension import OUT, persist

parser = argparse.ArgumentParser()
parser.add_argument("phase", choices=["acquire", "h8"])
args = parser.parse_args()
if args.phase == "acquire":
    _, source = acquire_spy()
    print(source)
else:
    result = run_h8()
    digest = persist(OUT/"h8.json", result)
    print({"phase": "h8", "n": result["n_signals"], "sha256": digest})
