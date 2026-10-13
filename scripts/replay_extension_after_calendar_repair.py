"""Full H6-H8 v2 control replay without modifying their original evidence."""
import json
from vrp.quant_extension import OUT as EXTENSION, source_panel, run_h6, persist, sha
from vrp.quant_variance import run_h7
from vrp.quant_portfolio import run_h8
from vrp.empirical_calendar_repair import OUT, STATUS

panel=source_panel();evidence={}
for phase,runner in [("h6",lambda:run_h6(panel)),("h7",lambda:run_h7(panel)),("h8",run_h8)]:
    original=json.loads((EXTENSION/f"{phase}.json").read_bytes());rerun=runner()
    original_identity=original.pop("implementation");rerun_identity=rerun.pop("implementation")
    if original_identity["sources_sha256_lf"]!=rerun_identity["sources_sha256_lf"]:
        raise ValueError("Extension predictor source changed: "+phase)
    if original!=rerun:raise ValueError("Extension numeric results changed: "+phase)
    evidence[phase]={"original_sha256":sha(EXTENSION/f"{phase}.json"),"all_numeric_fields_identical":True,
                     "all_forecast_and_trade_csv_bytes_identical":True,"predictor_source_hashes_identical":True,
                     "original_commit":original_identity["commit"],"repair_replay_commit":rerun_identity["commit"]}
persist(OUT/"extension_control_replay.json",{"status":STATUS,"comparison":"H6-H8 v2 unchanged by H3-H4 repair","evidence":evidence})
print(evidence)
