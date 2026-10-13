"""Explicit author-authorized statistical execution on the unchanged freeze."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
from scipy.stats import chi2, norm

from vrp.data import write_immutable
from vrp.inference import fit_hac_ols, newey_west_mean, nonoverlapping_origins_30c, overlap_l0
from vrp.interim_panel import code_identity, verify_interim
from vrp.processed_panel import PanelProvenanceError, _verified_artifact

STATUS = "PROVISIONAL — PENDING INDEPENDENT COAUTHOR REVIEW"
AUTHORIZATION = {"date": "2026-10-13", "authorized_by": "Aleksandar Slavov",
    "scope": "provisional H1-H5 before independent freeze review", "independent_review": "PENDING",
    "results_visible_before_review": True, "version": "provisional-h1-h5-execution/1.0.0"}
FREEZE_PATH = Path("data/processed/interim/40113d6646b0e7b8/interim_manifest.json")
EMPIRICAL_PATH = FREEZE_PATH.parent / "targets/bd7a172882ded86f/empirical_manifest.json"
FREEZE_SHA = "1fc80bde23388d5619ea876ed31142b398dc28b254abf3ea74fd7a03dc815ac4"
EMPIRICAL_SHA = "00532571aad5f8d9c43231933429fe6facbf7687a6332231ac8b7ad0ff73ccd9"


def identity(commit, files):
    base = code_identity(commit)
    root = Path(__file__).resolve().parents[2]
    for file in files:
        raw = (root/file).read_bytes().replace(b"\r\n",b"\n")
        saved = subprocess.run(["git","show",f"{commit}:{file}"],cwd=root,capture_output=True)
        if saved.returncode or saved.stdout.replace(b"\r\n",b"\n") != raw:
            raise PanelProvenanceError("Analysis code differs from commit: "+file)
        base["source_sha256_lf"][file] = hashlib.sha256(raw).hexdigest()
    return base


def inputs(root=Path(".")):
    root = root.resolve(); frozen = root/FREEZE_PATH; empirical = root/EMPIRICAL_PATH
    if hashlib.sha256(frozen.read_bytes()).hexdigest()!=FREEZE_SHA or hashlib.sha256(empirical.read_bytes()).hexdigest()!=EMPIRICAL_SHA:
        raise PanelProvenanceError("Pinned interim/empirical manifest mismatch")
    panel, spx, freeze = verify_interim(root/"data/raw",root/"data/processed",frozen,
        root/"data/manifests/2026-10-13_interim_authorization.json")
    report=json.loads(empirical.read_bytes())
    for name, info in report["outputs"].items(): _verified_artifact(root/"data/processed",info,name)
    if report["freeze_manifest_sha256"]!=FREEZE_SHA or len(panel)!=9064:
        raise PanelProvenanceError("Analysis freeze mismatch")
    output=report["outputs"]
    targets=pd.read_csv(root/"data/processed"/output["six_forward_targets.csv"]["relative_path"],float_precision="round_trip")
    daily=pd.read_csv(root/"data/processed"/output["canonical_daily.csv"]["relative_path"],float_precision="round_trip")
    if targets.origin.tolist()!=panel.origin.tolist() or daily.Date.tolist()!=spx.Date.tolist():
        raise PanelProvenanceError("Analysis date identity mismatch")
    if not report["audit"]["status"].startswith("PASSED_ALL"):
        raise PanelProvenanceError("Target audit not passed")
    return targets,daily,report


def checked_regression(y, x, lag, restriction=None, null=None):
    """Statsmodels HAC fit independently checked by numpy score sandwich."""
    y=np.asarray(y,float); x=np.asarray(x,float)
    if x.ndim==1: x=x[:,None]
    fit=fit_hac_ols(y,x,maxlags=lag)
    design=np.column_stack([np.ones(len(y)),x]); n,k=design.shape
    beta=np.linalg.lstsq(design,y,rcond=None)[0]; residual=y-design@beta
    score=design*residual[:,None]; meat=score.T@score
    for l in range(1,lag+1):
        cross=score[l:].T@score[:-l]; meat+=(1-l/(lag+1))*(cross+cross.T)
    bread=np.linalg.inv(design.T@design); covariance=bread@meat@bread*n/(n-k)
    if not np.allclose(beta,fit.params,rtol=1e-9,atol=1e-12) or not np.allclose(covariance,fit.cov_params(),rtol=1e-8,atol=1e-13):
        raise ValueError("Independent OLS/HAC score-sandwich mismatch")
    ci=fit.conf_int(); se=np.sqrt(np.diag(covariance)); p=2*norm.sf(np.abs(beta/se))
    if not np.allclose(p,fit.pvalues,rtol=1e-7,atol=1e-13): raise ValueError("Independent normal p-value mismatch")
    result={"n":n,"lag":lag,"coefficients":beta.tolist(),"se":fit.bse.tolist(),"ci95":ci.tolist(),
        "p_values":fit.pvalues.tolist(),"r_squared":float(fit.rsquared),
        "design_rank":int(np.linalg.matrix_rank(design)),"design_condition_number":float(np.linalg.cond(design)),
        "predictor_correlation":np.corrcoef(x.T).tolist() if x.shape[1]>1 else None,
        "independent_covariance_max_error":float(np.max(np.abs(covariance-fit.cov_params()))),
        "residual_mean":float(residual.mean()),"independent_verification":"PASSED_NUMPY_SCORE_SANDWICH"}
    if restriction is not None:
        R=np.asarray(restriction,float); q=np.asarray(null,float); delta=R@beta-q
        statistic=float(delta@np.linalg.solve(R@covariance@R.T,delta))
        wald=fit.wald_test((R,q),use_f=False,scalar=True)
        if not np.isclose(statistic,float(wald.statistic),rtol=1e-8,atol=1e-10): raise ValueError("Wald oracle mismatch")
        pvalue=float(chi2.sf(statistic,len(q)))
        result["wald"]={"statistic":statistic,"df":len(q),"p_value":pvalue,"restriction":R.tolist(),"null":q.tolist()}
    return result


def checked_mean(values,lag):
    fit=newey_west_mean(values,lag)
    oracle=checked_regression(values,np.empty((len(values),0)),lag)
    if not np.isclose(fit["standard_error"],oracle["se"][0],rtol=1e-10,atol=1e-14):
        raise ValueError("Independent mean HAC mismatch")
    a=np.asarray(values,float)
    return {**fit,"median":float(np.median(a)),"proportion_positive":float(np.mean(a>0)),
        "sample_sd":float(a.std(ddof=1)),"standardized_mean_effect":float(a.mean()/a.std(ddof=1)),
        "independent_verification":"PASSED_NUMPY_SCORE_SANDWICH"}


def run_h1_h2(targets):
    h1=[];h2=[]
    for subset,lower in {"full":"1990-01-02","post2003":"2004-01-01","post2014":"2014-10-06"}.items():
        sample=targets.loc[targets.origin>=lower]; l0=overlap_l0(sample.origin.tolist())
        for horizon in ("30c","21t"):
            lags=[l0,42,63] if horizon=="30c" else [20,10,21,42]
            for family in ("cc","parkinson","gk"):
                for lag in dict.fromkeys(lags):
                    label={"subset":subset,"family":family,"horizon":horizon,"lag":lag,"l0":l0}
                    for object_ in ("vrp_x","volgap"):
                        values=sample[f"{object_}_{family}_{horizon}"].to_numpy()
                        h1.append({**label,"object":object_,**checked_mean(values,lag)})
                    h2.append({**label,**checked_regression(sample[f"rvar_{family}_fwd_{horizon}"],
                        sample.ivar,lag,np.eye(2),[0,1])})
        selected={d.isoformat() for d in nonoverlapping_origins_30c(sample.origin.tolist())}
        nonoverlap=sample.loc[sample.origin.isin(selected)]
        for family in ("cc","parkinson","gk"):
            for object_ in ("vrp_x","volgap"):
                h1.append({"subset":subset,"family":family,"horizon":"30c_nonoverlap","object":object_,
                    **checked_mean(nonoverlap[f"{object_}_{family}_30c"],0)})
            h2.append({"subset":subset,"family":family,"horizon":"30c_nonoverlap",
                **checked_regression(nonoverlap[f"rvar_{family}_fwd_30c"],nonoverlap.ivar,0,np.eye(2),[0,1])})
    return {"status":STATUS,"authorization":AUTHORIZATION,"h1":h1,"h2":h2}


def persist(path,obj):
    return write_immutable(path,(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+"\n").encode())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code-commit",required=True);parser.add_argument("--parser-path",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True);args=parser.parse_args()
    sys.path.insert(0,str(args.parser_path.resolve()))
    ident=identity(args.code_commit,["src/vrp/provisional_analysis.py","src/vrp/inference.py"])
    targets,daily,empirical=inputs();result=run_h1_h2(targets)
    result.update({"implementation":ident,"freeze_sha256":FREEZE_SHA,"target_manifest_sha256":EMPIRICAL_SHA})
    print("H1/H2",persist(args.output,result),"L0",result["h1"][0]["l0"],flush=True)


if __name__=="__main__":main()
