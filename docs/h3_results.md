# h3 results

**PROVISIONAL — PENDING INDEPENDENT COAUTHOR REVIEW**

Aleksandar authorized provisional execution before Venelin's independent review on 2026-10-13. No independent acceptance/signature is implied. Protocol 1.1.0 and interim amendment remain fixed.

Input freeze SHA-256 `1fc80bde23388d5619ea876ed31142b398dc28b254abf3ea74fd7a03dc815ac4`; target manifest SHA-256 `00532571aad5f8d9c43231933429fe6facbf7687a6332231ac8b7ad0ff73ccd9`. Result source hashes: `h1_h2.json: 6b07e43199d3ffd723e42c8ed3bf497c800421f79a6c56b33b95d9e9d67d5a25`, `h3_h4.json: 03afa02ed0e6087ab507fcde105a066b591b74b10a9826cce553ce4310d5a1a5`, `h5.json: b2945442db51261cc5fde5555eab806e8413b35dc26a5292cfe6d80f49937b90`, `execution_audit.json: a37a4b74db24de665e0d1e109f237367a8f2c0110ada5d4a0ea8e106f38caeb6`.

Point estimates use the frozen untrimmed sample; Bartlett HAC finite-sample correction N/(N-k), asymptotic normal confidence intervals/p-values, joint Wald chi-square where specified. Independent numpy least-squares and score-sandwich checks passed. Numeric p=0 in diagnostics means floating-point underflow, not a mathematical zero. Full numerical precision is retained in source JSON.

## H3: recursive OOS variance forecasting

Initial training contains all valid returns through final 2006 session; each 2007-2025 origin is re-estimated using only returns through that origin. Constant-mean GARCH(1,1), percentage fit returns, decimal forecast variance /10000, analytic daily forecasts mapped to exact forward XNYS sessions. Cold defaults, maxiter=1000, ftol=1e-9 fixed before fits. Gaussian expanding is primary; Student-t expanding and Gaussian five-calendar-year rolling are robustness. Both horizons reuse each same fit. No model replacement on failures.

All three variants completed 4780/4780 origins (14340 fits), zero failures; all model comparisons and H4 use exactly their same 4780-origin common mask. Every daily forecast was independently checked by analytical recurrence, with final-residual forecast backcasts. Full checkpoint replay reused every verified record; 15 date-fixed fresh refits independently matched parameters, forecasts, warnings and residual diagnostics exactly.

Primary paired loss differential is squared loss(VIX) minus squared loss(GARCH); negative favors VIX. Mean=-0.0004917178918289112; HAC SE=0.000538406826985103; 95% CI=[-0.001546975882, 0.0005635400981]; p=0.36109363333697164. VIX has smaller RMSE but the paired primary advantage is not significant. GARCH has smaller MAE. No complete superiority or market-efficiency conclusion follows. QLIKE is separately defined as RVAR/forecast-log(RVAR/forecast)-1; all inputs positive.

| Variant | Horizon | Model | N | RMSE | MAE | Mean error actual-forecast | Bias forecast-actual | QLIKE |
|---|---|---|---|---|---|---|---|---|
| normal_expanding | 21t | garch | 4780 | 0.07247846183 | 0.02495735096 | 0.001020392421 | -0.001020392421 | 0.3878433838 |
| normal_expanding | 21t | naive | 4780 | 0.08254970268 | 0.02813174553 | 2.152779989e-05 | -2.152779989e-05 | 0.5830141402 |
| normal_expanding | 21t | vix | 4780 | 0.0681029251 | 0.02821372725 | -0.00737965085 | 0.00737965085 | 0.3719843004 |
| normal_expanding | 30c | garch | 4780 | 0.07212886308 | 0.02480491003 | 0.001109627106 | -0.001109627106 | 0.3806134368 |
| normal_expanding | 30c | naive | 4780 | 0.08422313065 | 0.02872896877 | -0.000873642923 | 0.000873642923 | 0.5767636154 |
| normal_expanding | 30c | vix | 4780 | 0.06863566855 | 0.02832637176 | -0.007471895198 | 0.007471895198 | 0.3702347242 |
| t_expanding | 21t | garch | 4780 | 0.07684945337 | 0.02665622273 | -0.001765834542 | 0.001765834542 | 0.4029653666 |
| t_expanding | 21t | naive | 4780 | 0.08254970268 | 0.02813174553 | 2.152779989e-05 | -2.152779989e-05 | 0.5830141402 |
| t_expanding | 21t | vix | 4780 | 0.0681029251 | 0.02821372725 | -0.00737965085 | 0.00737965085 | 0.3719843004 |
| t_expanding | 30c | garch | 4780 | 0.07632804896 | 0.02649753826 | -0.001630622997 | 0.001630622997 | 0.3952699742 |
| t_expanding | 30c | naive | 4780 | 0.08422313065 | 0.02872896877 | -0.000873642923 | 0.000873642923 | 0.5767636154 |
| t_expanding | 30c | vix | 4780 | 0.06863566855 | 0.02832637176 | -0.007471895198 | 0.007471895198 | 0.3702347242 |
| normal_rolling5y | 21t | garch | 4780 | 0.07161450588 | 0.02539972544 | 0.0002967758715 | -0.0002967758715 | 0.4098275468 |
| normal_rolling5y | 21t | naive | 4780 | 0.08254970268 | 0.02813174553 | 2.152779989e-05 | -2.152779989e-05 | 0.5830141402 |
| normal_rolling5y | 21t | vix | 4780 | 0.0681029251 | 0.02821372725 | -0.00737965085 | 0.00737965085 | 0.3719843004 |
| normal_rolling5y | 30c | garch | 4780 | 0.07129255329 | 0.02520358047 | 0.0003968723657 | -0.0003968723657 | 0.4012937697 |
| normal_rolling5y | 30c | naive | 4780 | 0.08422313065 | 0.02872896877 | -0.000873642923 | 0.000873642923 | 0.5767636154 |
| normal_rolling5y | 30c | vix | 4780 | 0.06863566855 | 0.02832637176 | -0.007471895198 | 0.007471895198 | 0.3702347242 |

| Variant | Converged | Failed | Warning origins | Persistence median | Min | Max | ≥0.99 | ≥1 |
|---|---|---|---|---|---|---|---|---|
| normal_expanding | 4780 | 0 | 38 | 0.9893737511 | 0.9835113603 | 0.9958352744 | 2206 | 0 |
| t_expanding | 4780 | 0 | 38 | 0.9965934886 | 0.994703022 | 0.9996461366 | 4780 | 0 |
| normal_rolling5y | 4780 | 0 | 38 | 0.9803921579 | 0.8796408712 | 1 | 1239 | 3 |

Warning logs distinguish library FutureWarnings from convergence failures; none failed. Near-unit persistence is common, especially Student-t; three rolling fits are at/just above one within floating-point precision and are retained. Residual diagnostics use 38 pre-selected calendar anchors per variant, not every fit; they are not a claim that all residual ARCH disappeared.

| Variant | Horizon | Lag | Contrast | Mean squared-loss difference | HAC SE | 95% CI | Raw p | Holm p (two secondary contrasts only) |
|---|---|---|---|---|---|---|---|---|
| normal_expanding | 21t | 20 | garch_vs_naive | -0.001561325983 | 0.001024441913 | [-0.003569195237, 0.0004465432702] | 0.1274900562483036 | 0.2549801124966072 |
| normal_expanding | 21t | 20 | vix_vs_garch | -0.0006151190223 | 0.0005541012283 | [-0.001701137474, 0.000470899429] | 0.26694719030823655 | 'primary: unadjusted' |
| normal_expanding | 21t | 20 | vix_vs_naive | -0.002176445005 | 0.001509697638 | [-0.005135398003, 0.0007825079924] | 0.14940311621656083 | 0.2549801124966072 |
| normal_expanding | 21t | 10 | garch_vs_naive | -0.001561325983 | 0.0008993911612 | [-0.003324100267, 0.0002014483008] | 0.08256719104439153 | 0.1623514265091107 |
| normal_expanding | 21t | 10 | vix_vs_garch | -0.0006151190223 | 0.0004608914391 | [-0.001518449644, 0.000288211599] | 0.18199784297277743 | 'primary: unadjusted' |
| normal_expanding | 21t | 10 | vix_vs_naive | -0.002176445005 | 0.001248029801 | [-0.004622538468, 0.0002696484567] | 0.08117571325455535 | 0.1623514265091107 |
| normal_expanding | 21t | 21 | garch_vs_naive | -0.001561325983 | 0.001031797662 | [-0.003583612239, 0.0004609602731] | 0.13022646187066386 | 0.2604529237413277 |
| normal_expanding | 21t | 21 | vix_vs_garch | -0.0006151190223 | 0.0005598534894 | [-0.001712411698, 0.0004821736535] | 0.2718927127784463 | 'primary: unadjusted' |
| normal_expanding | 21t | 21 | vix_vs_naive | -0.002176445005 | 0.001525480201 | [-0.00516633126, 0.0008134412486] | 0.1536583704628995 | 0.2604529237413277 |
| normal_expanding | 21t | 42 | garch_vs_naive | -0.001561325983 | 0.001131549214 | [-0.003779121689, 0.0006564697231] | 0.16764431942101343 | 0.33528863884202686 |
| normal_expanding | 21t | 42 | vix_vs_garch | -0.0006151190223 | 0.0006235350861 | [-0.001837225334, 0.0006069872896] | 0.3238865095934764 | 'primary: unadjusted' |
| normal_expanding | 21t | 42 | vix_vs_naive | -0.002176445005 | 0.001718015825 | [-0.005543694148, 0.001190804137] | 0.2052137891086102 | 0.33528863884202686 |
| normal_expanding | 30c | 21 | garch_vs_naive | -0.001890962848 | 0.001153745999 | [-0.004152263453, 0.0003703377581] | 0.10121810560425824 | 0.2024362112085165 |
| normal_expanding | 30c | 21 | vix_vs_garch | -0.0004917178918 | 0.000538406827 | [-0.001546975882, 0.0005635400981] | 0.36109363333697164 | 'primary: unadjusted' |
| normal_expanding | 30c | 21 | vix_vs_naive | -0.002382680739 | 0.001633093864 | [-0.005583485897, 0.0008181244181] | 0.14456564847424458 | 0.2024362112085165 |
| normal_expanding | 30c | 42 | garch_vs_naive | -0.001890962848 | 0.001271481663 | [-0.004383021115, 0.0006010954199] | 0.13695881526480422 | 0.27391763052960844 |
| normal_expanding | 30c | 42 | vix_vs_garch | -0.0004917178918 | 0.0006019343418 | [-0.001671487523, 0.0006880517392] | 0.4139877350219736 | 'primary: unadjusted' |
| normal_expanding | 30c | 42 | vix_vs_naive | -0.002382680739 | 0.001834131535 | [-0.005977512491, 0.001212151013] | 0.19391701021501773 | 0.27391763052960844 |
| normal_expanding | 30c | 63 | garch_vs_naive | -0.001890962848 | 0.001309301898 | [-0.004457147413, 0.000675221718] | 0.1486678957879451 | 0.2973357915758902 |
| normal_expanding | 30c | 63 | vix_vs_garch | -0.0004917178918 | 0.0006166714009 | [-0.001700371628, 0.0007169358443] | 0.4252337133073407 | 'primary: unadjusted' |
| normal_expanding | 30c | 63 | vix_vs_naive | -0.002382680739 | 0.001893648096 | [-0.006094162807, 0.001328801329] | 0.20830173509867245 | 0.2973357915758902 |
| t_expanding | 21t | 20 | garch_vs_naive | -0.0009086149288 | 0.0006864426541 | [-0.002254017808, 0.0004367879507] | 0.1856168379864368 | 0.29880623243312165 |
| t_expanding | 21t | 20 | vix_vs_garch | -0.001267830077 | 0.0009128936249 | [-0.003057068703, 0.0005214085497] | 0.16489243891575767 | 'primary: unadjusted' |
| t_expanding | 21t | 20 | vix_vs_naive | -0.002176445005 | 0.001509697638 | [-0.005135398003, 0.0007825079924] | 0.14940311621656083 | 0.29880623243312165 |
| t_expanding | 21t | 10 | garch_vs_naive | -0.0009086149288 | 0.000675934875 | [-0.00223342294, 0.0004161930822] | 0.17887259258877497 | 0.17887259258877497 |
| t_expanding | 21t | 10 | vix_vs_garch | -0.001267830077 | 0.0007487026495 | [-0.002735260305, 0.0001996001515] | 0.09038519591913823 | 'primary: unadjusted' |
| t_expanding | 21t | 10 | vix_vs_naive | -0.002176445005 | 0.001248029801 | [-0.004622538468, 0.0002696484567] | 0.08117571325455535 | 0.1623514265091107 |
| t_expanding | 21t | 21 | garch_vs_naive | -0.0009086149288 | 0.0006867651116 | [-0.002254649813, 0.0004374199559] | 0.18582342435183286 | 0.307316740925799 |
| t_expanding | 21t | 21 | vix_vs_garch | -0.001267830077 | 0.000923073831 | [-0.003077021541, 0.0005413613872] | 0.16960094276250182 | 'primary: unadjusted' |
| t_expanding | 21t | 21 | vix_vs_naive | -0.002176445005 | 0.001525480201 | [-0.00516633126, 0.0008134412486] | 0.1536583704628995 | 0.307316740925799 |
| t_expanding | 21t | 42 | garch_vs_naive | -0.0009086149288 | 0.0007278193129 | [-0.002335114569, 0.0005178847118] | 0.2118819443559632 | 0.4104275782172204 |
| t_expanding | 21t | 42 | vix_vs_garch | -0.001267830077 | 0.001033734144 | [-0.003293911769, 0.0007582516159] | 0.2200268931826771 | 'primary: unadjusted' |
| t_expanding | 21t | 42 | vix_vs_naive | -0.002176445005 | 0.001718015825 | [-0.005543694148, 0.001190804137] | 0.2052137891086102 | 0.4104275782172204 |
| t_expanding | 30c | 21 | garch_vs_naive | -0.001267564678 | 0.0008083607234 | [-0.002851922583, 0.0003167932264] | 0.11686523612934753 | 0.23373047225869506 |
| t_expanding | 30c | 21 | vix_vs_garch | -0.001115116061 | 0.0008867712261 | [-0.002853155727, 0.0006229236044] | 0.20857213117567786 | 'primary: unadjusted' |
| t_expanding | 30c | 21 | vix_vs_naive | -0.002382680739 | 0.001633093864 | [-0.005583485897, 0.0008181244181] | 0.14456564847424458 | 0.23373047225869506 |
| t_expanding | 30c | 42 | garch_vs_naive | -0.001267564678 | 0.0008724918318 | [-0.002977617245, 0.000442487889] | 0.1462765720025297 | 0.2925531440050594 |
| t_expanding | 30c | 42 | vix_vs_garch | -0.001115116061 | 0.0009947490244 | [-0.003064788323, 0.0008345562002] | 0.2622868333126932 | 'primary: unadjusted' |
| t_expanding | 30c | 42 | vix_vs_naive | -0.002382680739 | 0.001834131535 | [-0.005977512491, 0.001212151013] | 0.19391701021501773 | 0.2925531440050594 |
| t_expanding | 30c | 63 | garch_vs_naive | -0.001267564678 | 0.0008949257551 | [-0.003021586927, 0.0004864575708] | 0.15666109254727636 | 0.31332218509455273 |
| t_expanding | 30c | 63 | vix_vs_garch | -0.001115116061 | 0.001022620891 | [-0.003119416178, 0.0008891840554] | 0.27551534999747884 | 'primary: unadjusted' |
| t_expanding | 30c | 63 | vix_vs_naive | -0.002382680739 | 0.001893648096 | [-0.006094162807, 0.001328801329] | 0.20830173509867245 | 0.31332218509455273 |
| normal_rolling5y | 21t | 20 | garch_vs_naive | -0.00168581596 | 0.001246319083 | [-0.004128556475, 0.0007569245548] | 0.1761719708587105 | 0.29880623243312165 |
| normal_rolling5y | 21t | 20 | vix_vs_garch | -0.0004906290453 | 0.0004660232901 | [-0.00140401791, 0.0004227598192] | 0.29243293496446265 | 'primary: unadjusted' |
| normal_rolling5y | 21t | 20 | vix_vs_naive | -0.002176445005 | 0.001509697638 | [-0.005135398003, 0.0007825079924] | 0.14940311621656083 | 0.29880623243312165 |
| normal_rolling5y | 21t | 10 | garch_vs_naive | -0.00168581596 | 0.001140874661 | [-0.003921889206, 0.000550257286] | 0.13950089294376913 | 0.1623514265091107 |
| normal_rolling5y | 21t | 10 | vix_vs_garch | -0.0004906290453 | 0.0004517920032 | [-0.0013761251, 0.0003948670094] | 0.2774957087224772 | 'primary: unadjusted' |
| normal_rolling5y | 21t | 10 | vix_vs_naive | -0.002176445005 | 0.001248029801 | [-0.004622538468, 0.0002696484567] | 0.08117571325455535 | 0.1623514265091107 |
| normal_rolling5y | 21t | 21 | garch_vs_naive | -0.00168581596 | 0.001251831422 | [-0.004139360461, 0.0007677285409] | 0.1780834137781392 | 0.307316740925799 |
| normal_rolling5y | 21t | 21 | vix_vs_garch | -0.0004906290453 | 0.0004665842919 | [-0.001405117453, 0.0004238593626] | 0.29301360055932524 | 'primary: unadjusted' |
| normal_rolling5y | 21t | 21 | vix_vs_naive | -0.002176445005 | 0.001525480201 | [-0.00516633126, 0.0008134412486] | 0.1536583704628995 | 0.307316740925799 |
| normal_rolling5y | 21t | 42 | garch_vs_naive | -0.00168581596 | 0.001352172057 | [-0.004336024493, 0.0009643925724] | 0.21249041382613187 | 0.4104275782172204 |
| normal_rolling5y | 21t | 42 | vix_vs_garch | -0.0004906290453 | 0.0004639567932 | [-0.00139996765, 0.0004187095597] | 0.2902886295012762 | 'primary: unadjusted' |
| normal_rolling5y | 21t | 42 | vix_vs_naive | -0.002176445005 | 0.001718015825 | [-0.005543694148, 0.001190804137] | 0.2052137891086102 | 0.4104275782172204 |
| normal_rolling5y | 30c | 21 | garch_vs_naive | -0.002010907581 | 0.001362306753 | [-0.004680979754, 0.0006591645909] | 0.13991575189490554 | 0.2798315037898111 |
| normal_rolling5y | 30c | 21 | vix_vs_garch | -0.000371773158 | 0.0004515596909 | [-0.001256813889, 0.0005132675729] | 0.4103322962799131 | 'primary: unadjusted' |
| normal_rolling5y | 30c | 21 | vix_vs_naive | -0.002382680739 | 0.001633093864 | [-0.005583485897, 0.0008181244181] | 0.14456564847424458 | 0.2798315037898111 |
| normal_rolling5y | 30c | 42 | garch_vs_naive | -0.002010907581 | 0.00148149966 | [-0.004914593558, 0.0008927783954] | 0.17467130967253297 | 0.34934261934506594 |
| normal_rolling5y | 30c | 42 | vix_vs_garch | -0.000371773158 | 0.0004467815482 | [-0.001247448901, 0.0005039025854] | 0.4053446295157791 | 'primary: unadjusted' |
| normal_rolling5y | 30c | 42 | vix_vs_naive | -0.002382680739 | 0.001834131535 | [-0.005977512491, 0.001212151013] | 0.19391701021501773 | 0.34934261934506594 |
| normal_rolling5y | 30c | 63 | garch_vs_naive | -0.002010907581 | 0.001519192684 | [-0.004988470528, 0.0009666553651] | 0.1856131469204254 | 0.3712262938408508 |
| normal_rolling5y | 30c | 63 | vix_vs_garch | -0.000371773158 | 0.0004391999284 | [-0.0012325892, 0.0004890428836] | 0.39728603879431934 | 'primary: unadjusted' |
| normal_rolling5y | 30c | 63 | vix_vs_naive | -0.002382680739 | 0.001893648096 | [-0.006094162807, 0.001328801329] | 0.20830173509867245 | 0.3712262938408508 |

Parameter distributions, per-origin warnings/convergence, standardized residual JB/Ljung-Box/ARCH-LM diagnostics and QLIKE contrast uncertainties are in the hashed source JSON and local forecast checkpoints. Raw and adjusted p-values are retained.
