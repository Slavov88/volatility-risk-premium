"""Execute committed registered H6/H7 against hash-verified baseline inputs."""
import argparse
from vrp.quant_extension import OUT, source_panel, run_h6, persist

parser = argparse.ArgumentParser()
parser.add_argument("phase", choices=["h6", "h7"])
args = parser.parse_args()
panel = source_panel()
if args.phase == "h6":
    result = run_h6(panel)
else:
    from vrp.quant_variance import run_h7
    result = run_h7(panel)
digest = persist(OUT/f"{args.phase}.json", result)
print({"phase": args.phase, "n": result["n"], "sha256": digest, "failed_fits": result["failed_fits"]})
