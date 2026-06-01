import pandas as pd
import numpy as np

LOG_PATH = 'c:/Users/lenovo/Desktop/btc-quant/research/phase1b_episode_research_log.csv'
OBS_PATH = 'c:/Users/lenovo/Desktop/btc-quant/outputs/historical_observation_rows.csv'

log = pd.read_csv(LOG_PATH)
obs = pd.read_csv(OBS_PATH)

for c in ['price_zscore', 'price_mean_shift', 'distribution_shift_strength', 'delta_zscore']:
    if c in obs.columns:
        obs[c] = pd.to_numeric(obs[c], errors='coerce')

obs['row_id'] = pd.to_numeric(obs['row_id'], errors='coerce')
log['start_row_id'] = pd.to_numeric(log['start_row_id'], errors='coerce')
obs_sorted = obs.sort_values('row_id').reset_index(drop=True)

# Build a dict keyed by row_id for fast lookup
obs_dict = obs.set_index('row_id').to_dict('index')

fields = ['price_zone', 'price_zscore', 'price_mean_shift',
          'delta_pressure_state', 'aggressive_flow', 'gaussian_tail',
          'distribution_shift_state', 'distribution_shift_strength', 'delta_zscore']

joined_data = {f'obs_{f}': [] for f in fields}
for _, row in log.iterrows():
    rid = row['start_row_id']
    if pd.isna(rid) or rid not in obs_dict:
        for f in fields:
            joined_data[f'obs_{f}'].append(None)
    else:
        rec = obs_dict[rid]
        for f in fields:
            joined_data[f'obs_{f}'].append(rec.get(f))

for k, v in joined_data.items():
    log[k] = v

log['obs_price_zscore'] = pd.to_numeric(log['obs_price_zscore'], errors='coerce')
log['obs_price_mean_shift'] = pd.to_numeric(log['obs_price_mean_shift'], errors='coerce')

# Slow ZScore proxy: mean price_zscore of last 50 rows before episode start
obs_sorted['price_zscore'] = pd.to_numeric(obs_sorted['price_zscore'], errors='coerce')
row_ids_sorted = obs_sorted['row_id'].values
pzscores = obs_sorted['price_zscore'].values

def slow_zscore_proxy(start_rid):
    if pd.isna(start_rid):
        return None
    mask = row_ids_sorted < start_rid
    idx = np.where(mask)[0]
    if len(idx) < 5:
        return None
    window_idx = idx[-50:]
    vals = pzscores[window_idx]
    vals = vals[~np.isnan(vals)]
    if len(vals) < 5:
        return None
    return float(np.mean(vals))

log['slow_zscore_proxy'] = log['start_row_id'].apply(slow_zscore_proxy)

# Vote functions
def price_zone_vote(pz):
    if pz is None or (isinstance(pz, float) and np.isnan(pz)):
        return None
    pz = str(pz)
    if pz in ('EXTREME_HIGH_ZONE', 'HIGH_STATISTICAL_ZONE'):
        return 'BULLISH'
    if pz in ('EXTREME_LOW_ZONE', 'LOW_STATISTICAL_ZONE'):
        return 'BEARISH'
    return 'NO_SIGNAL'

def pzscore_vote(v):
    try:
        v = float(v)
    except Exception:
        return None
    if v > 0.5:
        return 'BULLISH'
    if v < -0.5:
        return 'BEARISH'
    return 'NO_SIGNAL'

def slow_vote(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    if v > 0.3:
        return 'BULLISH'
    if v < -0.3:
        return 'BEARISH'
    return 'NO_SIGNAL'

def delta_press_vote(s):
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return None
    s = str(s)
    if 'BUY' in s:
        return 'BULLISH'
    if 'SELL' in s:
        return 'BEARISH'
    return 'NO_SIGNAL'

def agg_flow_vote(s):
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return None
    s = str(s)
    if 'BUYERS' in s:
        return 'BULLISH'
    if 'SELLERS' in s:
        return 'BEARISH'
    return 'NO_SIGNAL'

def mean_shift_vote(v):
    try:
        v = float(v)
    except Exception:
        return None
    if v > 0.2:
        return 'BULLISH'
    if v < -0.2:
        return 'BEARISH'
    return 'NO_SIGNAL'

log['vote_price_zone'] = log['obs_price_zone'].apply(price_zone_vote)
log['vote_pzscore'] = log['obs_price_zscore'].apply(pzscore_vote)
log['vote_slow_zscore'] = log['slow_zscore_proxy'].apply(slow_vote)
log['vote_delta_press'] = log['obs_delta_pressure_state'].apply(delta_press_vote)
log['vote_agg_flow'] = log['obs_aggressive_flow'].apply(agg_flow_vote)
log['vote_mean_shift'] = log['obs_price_mean_shift'].apply(mean_shift_vote)

gt = log['future_direction']
total = len(log)

print(f'Total episodes: {total}')
print(f'future_direction UP: {(gt=="UP").sum()}  DOWN: {(gt=="DOWN").sum()}  other: {(~gt.isin(["UP","DOWN"])).sum()}')
print()

def validate(vote_col, df):
    votes = df[vote_col]
    gt_col = df['future_direction']

    has_signal = votes.isin(['BULLISH', 'BEARISH'])
    coverage_n = has_signal.sum()
    coverage_pct = coverage_n / total * 100

    no_signal_n = (~has_signal).sum()

    # Directional: restrict to episodes where gt is UP or DOWN
    dir_mask = gt_col.isin(['UP', 'DOWN'])
    d = df[dir_mask].copy()
    d_vote = d[vote_col]
    d_gt = d['future_direction']

    dir_has_signal = d_vote.isin(['BULLISH', 'BEARISH'])
    d2 = d[dir_has_signal]
    n_tested = len(d2)

    if n_tested == 0:
        return dict(coverage_n=int(coverage_n), coverage_pct=round(coverage_pct, 1),
                    n_tested=0, dir_acc=None, bull_acc=None, bear_acc=None,
                    false_pct=None, bullish_n=0, bearish_n=0,
                    false_bull=0, false_bear=0, no_signal_n=int(no_signal_n))

    correct = (
        ((d2[vote_col] == 'BULLISH') & (d2['future_direction'] == 'UP')) |
        ((d2[vote_col] == 'BEARISH') & (d2['future_direction'] == 'DOWN'))
    )
    dir_acc = correct.sum() / n_tested * 100

    bull_mask = d2[vote_col] == 'BULLISH'
    bear_mask = d2[vote_col] == 'BEARISH'
    bullish_n = bull_mask.sum()
    bearish_n = bear_mask.sum()

    bull_acc = ((d2.loc[bull_mask, 'future_direction'] == 'UP').sum() / bullish_n * 100
                if bullish_n > 0 else None)
    bear_acc = ((d2.loc[bear_mask, 'future_direction'] == 'DOWN').sum() / bearish_n * 100
                if bearish_n > 0 else None)

    false_bull = ((d2[vote_col] == 'BULLISH') & (d2['future_direction'] == 'DOWN')).sum()
    false_bear = ((d2[vote_col] == 'BEARISH') & (d2['future_direction'] == 'UP')).sum()
    total_false = false_bull + false_bear
    false_pct = total_false / n_tested * 100

    return dict(
        coverage_n=int(coverage_n), coverage_pct=round(coverage_pct, 1),
        n_tested=int(n_tested), dir_acc=round(dir_acc, 1),
        bull_acc=round(bull_acc, 1) if bull_acc is not None else None,
        bear_acc=round(bear_acc, 1) if bear_acc is not None else None,
        false_pct=round(false_pct, 1),
        bullish_n=int(bullish_n), bearish_n=int(bearish_n),
        false_bull=int(false_bull), false_bear=int(false_bear),
        no_signal_n=int(no_signal_n),
    )

variables = [
    ('price_zone',      'vote_price_zone'),
    ('price_zscore',    'vote_pzscore'),
    ('slow_zscore',     'vote_slow_zscore'),
    ('delta_pressure',  'vote_delta_press'),
    ('aggressive_flow', 'vote_agg_flow'),
    ('price_mean_shift','vote_mean_shift'),
]

results = {}
for name, col in variables:
    results[name] = validate(col, log)

print('=== VALIDATION RESULTS (ground truth = future_direction, UP/DOWN only) ===')
print()
fmt = '{:<22s}  {:>5s}  {:>7s}  {:>8s}  {:>8s}  {:>8s}  {:>7s}  {:>7s}  {:>7s}'
print(fmt.format('Variable', 'Cov%', 'N_test', 'Dir_Acc', 'Bull_Acc', 'Bear_Acc', 'False%', 'B_n', 'S_n'))
print('-' * 100)
for name, r in results.items():
    ba = f"{r['bull_acc']:.1f}" if r['bull_acc'] is not None else 'N/A'
    bea = f"{r['bear_acc']:.1f}" if r['bear_acc'] is not None else 'N/A'
    da = f"{r['dir_acc']:.1f}" if r['dir_acc'] is not None else 'N/A'
    fp = f"{r['false_pct']:.1f}" if r['false_pct'] is not None else 'N/A'
    print(fmt.format(
        name,
        f"{r['coverage_pct']:.0f}%",
        str(r['n_tested']),
        da + '%', ba + '%', bea + '%', fp + '%',
        str(r['bullish_n']), str(r['bearish_n'])
    ))

print()
print('=== VOTE DISTRIBUTIONS ===')
for name, col in variables:
    vc = log[col].value_counts(dropna=False)
    print(f'  {name}: {dict(vc)}')

print()
print('=== CROSS-TAB: vote vs future_direction (directional episodes only) ===')
dir_log = log[log['future_direction'].isin(['UP', 'DOWN'])]
for name, col in variables:
    ct = pd.crosstab(dir_log[col].fillna('NO_DATA'), dir_log['future_direction'])
    print(f'\n-- {name} --')
    print(ct.to_string())

print()
print('=== BASELINE ===')
print(f'Random chance (55.9% DOWN): 55.9% directional accuracy if always predict DOWN')
down_pct = (gt == 'DOWN').sum() / len(gt[gt.isin(['UP','DOWN'])]) * 100
print(f'Actual DOWN base rate: {down_pct:.1f}%')
