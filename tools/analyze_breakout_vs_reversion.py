import pandas as pd
import numpy as np

LOG = 'c:/Users/lenovo/Desktop/btc-quant/research/phase1b_episode_research_log.csv'
OBS = 'c:/Users/lenovo/Desktop/btc-quant/outputs/historical_observation_rows.csv'

log = pd.read_csv(LOG)
obs = pd.read_csv(OBS)

for c in ['price_zscore', 'delta_zscore', 'velocity', 'volume',
          'price_mean_shift', 'distribution_shift_strength', 'rvi']:
    if c in obs.columns:
        obs[c] = pd.to_numeric(obs[c], errors='coerce')
obs['row_id'] = pd.to_numeric(obs['row_id'], errors='coerce')
log['start_row_id'] = pd.to_numeric(log['start_row_id'], errors='coerce')
for c in ['max_abs_move_4h', 'max_abs_move_1h', 'peak_velocity', 'peak_delta_zscore']:
    if c in log.columns:
        log[c] = pd.to_numeric(log[c], errors='coerce')

obs_dict = obs.set_index('row_id').to_dict('index')

join_fields = ['price_zscore', 'delta_zscore', 'velocity', 'volume',
               'price_mean_shift', 'distribution_shift_strength',
               'distribution_shift_state', 'price_zone', 'delta_pressure_state',
               'velocity_state', 'volume_state', 'gaussian_zone',
               'gaussian_tail', 'rvi', 'volatility_regime']

joined = {}
for f in join_fields:
    if f in obs.columns:
        joined[f'obs_{f}'] = [
            obs_dict[float(r)].get(f) if not pd.isna(r) and float(r) in obs_dict else None
            for r in log['start_row_id']
        ]
log_aug = pd.concat([log, pd.DataFrame(joined, index=log.index)], axis=1)

for f in ['price_zscore', 'delta_zscore', 'velocity', 'volume',
          'price_mean_shift', 'distribution_shift_strength', 'rvi']:
    col = f'obs_{f}'
    if col in log_aug.columns:
        log_aug[col] = pd.to_numeric(log_aug[col], errors='coerce')

obs_sorted = obs.sort_values('row_id').reset_index(drop=True)
for c in ['price_zscore', 'close', 'delta', 'velocity', 'volume']:
    obs_sorted[c] = pd.to_numeric(obs_sorted[c], errors='coerce')

rid_arr = obs_sorted['row_id'].values
arr_pz = obs_sorted['price_zscore'].values
arr_cl = obs_sorted['close'].values
arr_dl = obs_sorted['delta'].values
arr_vl = obs_sorted['velocity'].values
arr_vm = obs_sorted['volume'].values


def pre_window_stats(rid, n=50):
    if pd.isna(rid):
        return {}
    idx = np.where(rid_arr < rid)[0]
    if len(idx) < 5:
        return {}
    w = idx[-n:] if len(idx) >= n else idx
    cl = arr_cl[w]; cl = cl[~np.isnan(cl)]
    pz = arr_pz[w]; pz = pz[~np.isnan(pz)]
    dl = arr_dl[w]; dl = dl[~np.isnan(dl)]
    vl = arr_vl[w]; vl = vl[~np.isnan(vl)]
    vm = arr_vm[w]; vm = vm[~np.isnan(vm)]
    if len(cl) < 5:
        return {}
    price_trend = float(cl[-1] - cl[0]) if len(cl) >= 2 else 0.0
    vol_accel = None
    if len(vm) >= 20 and float(np.mean(vm[:10])) > 0:
        vol_accel = float(np.mean(vm[-10:]) / np.mean(vm[:10]))
    vol_late = float(np.mean(vm[-10:])) if len(vm) >= 10 else None
    vol_early = float(np.mean(vm[:10])) if len(vm) >= 10 else None
    # zscore at equil: how many rows had |pzscore| < 0.5
    equil_rows = int(np.sum(np.abs(pz) < 0.5)) if len(pz) > 0 else 0
    return {
        'pre_mean_pzscore': float(np.mean(pz)) if len(pz) >= 5 else None,
        'pre_price_trend': price_trend,
        'pre_delta_mean': float(np.mean(dl)) if len(dl) >= 5 else None,
        'pre_delta_sum': float(np.sum(dl)) if len(dl) >= 5 else None,
        'pre_velocity_mean': float(np.mean(vl)) if len(vl) >= 5 else None,
        'pre_volume_mean': float(np.mean(vm)) if len(vm) >= 5 else None,
        'pre_volume_late': vol_late,
        'pre_volume_early': vol_early,
        'pre_volume_accel': vol_accel,
        'pre_equil_rows': equil_rows,
    }


stats_list = [pre_window_stats(r) for r in log_aug['start_row_id']]
stats_df = pd.DataFrame(stats_list, index=log_aug.index)
log_aug = pd.concat([log_aug, stats_df], axis=1)


def classify_type(row):
    fd = row.get('future_direction')
    pt = row.get('pre_price_trend') or 0.0
    if fd not in ('UP', 'DOWN'):
        return 'UNDETERMINED'
    pre_dir = 'UP' if pt > 30 else ('DOWN' if pt < -30 else 'FLAT')
    if pre_dir == fd:
        return 'CONTINUATION'
    if pre_dir == 'FLAT':
        return 'NEUTRAL_BREAKOUT'
    return 'MEAN_REVERSION'


log_aug['episode_type'] = log_aug.apply(classify_type, axis=1)

cont = log_aug[log_aug['episode_type'] == 'CONTINUATION'].copy()
rev = log_aug[log_aug['episode_type'] == 'MEAN_REVERSION'].copy()
neut = log_aug[log_aug['episode_type'] == 'NEUTRAL_BREAKOUT'].copy()

print(f'CONTINUATION n={len(cont)}  MEAN_REVERSION n={len(rev)}  NEUTRAL_BREAKOUT n={len(neut)}')
print()

metrics = [
    ('pre_mean_pzscore', 'Pre-episode mean price_zscore (50r)'),
    ('pre_price_trend', 'Pre-episode price trend 50r (points)'),
    ('pre_delta_mean', 'Pre-episode delta mean (50r)'),
    ('pre_delta_sum', 'Pre-episode cumulative delta (50r)'),
    ('pre_velocity_mean', 'Pre-episode velocity mean (50r)'),
    ('pre_volume_accel', 'Volume acceleration (last10/first10)'),
    ('pre_equil_rows', 'Rows with |pzscore|<0.5 in 50r window'),
    ('obs_price_zscore', 'price_zscore at trigger row'),
    ('obs_delta_zscore', 'delta_zscore at trigger row'),
    ('obs_velocity', 'velocity at trigger row'),
    ('obs_rvi', 'rvi at trigger row'),
    ('obs_distribution_shift_strength', 'dist_shift_strength at trigger'),
    ('max_abs_move_4h', 'max_abs_move_4h'),
    ('max_abs_move_1h', 'max_abs_move_1h'),
]

print(f'{"Metric":<48s}  {"CONT":>8s}  {"MR":>8s}  {"DIFF":>8s}')
print('-' * 80)
for col, label in metrics:
    if col not in log_aug.columns:
        continue
    try:
        cm_vals = pd.to_numeric(cont[col], errors='coerce').dropna()
        rm_vals = pd.to_numeric(rev[col], errors='coerce').dropna()
        if len(cm_vals) == 0 or len(rm_vals) == 0:
            continue
        c_mean = float(cm_vals.mean())
        r_mean = float(rm_vals.mean())
        diff = c_mean - r_mean
    except Exception:
        continue
    print(f'{label:<48s}  {c_mean:8.3f}  {r_mean:8.3f}  {diff:+8.3f}')

print()
print('=== price_zscore at trigger: CONT vs MR distribution ===')
for label, sub in [('CONT', cont), ('MR', rev)]:
    pz = sub['obs_price_zscore'].dropna()
    near_zero = ((pz.abs() < 0.5).sum())
    high = (pz > 1.0).sum()
    low = (pz < -1.0).sum()
    print(f'  {label}: n={len(pz)}  |pz|<0.5={near_zero}({near_zero/len(pz)*100:.0f}%)  pz>1={high}  pz<-1={low}')
    print(f'    mean={pz.mean():.3f}  median={pz.median():.3f}  std={pz.std():.3f}')

print()
print('=== CONTINUATION episodes: breakdown ===')
print(cont[['case_id', 'zone_type', 'future_direction', 'obs_price_zscore',
            'obs_delta_zscore', 'pre_price_trend', 'pre_delta_sum',
            'pre_volume_accel', 'max_abs_move_4h', 'classification']].to_string(index=False))

print()
print('=== NEUTRAL_BREAKOUT episodes (flat pre + directional outcome) ===')
print(neut[['case_id', 'zone_type', 'future_direction', 'obs_price_zscore',
            'obs_delta_zscore', 'pre_price_trend', 'max_abs_move_4h',
            'classification']].to_string(index=False))

print()
print('=== Distribution_shift breakdown: CONT vs MR ===')
for label, sub in [('CONT', cont), ('MR', rev)]:
    ds = sub['obs_distribution_shift_state'].value_counts(dropna=True)
    print(f'  {label}: {dict(ds)}')

print()
print('=== Volume acceleration: CONT vs MR ===')
for label, sub in [('CONT', cont), ('MR', rev)]:
    va = sub['pre_volume_accel'].dropna()
    above1 = (va > 1.1).sum()
    below1 = (va < 0.9).sum()
    print(f'  {label}: mean={va.mean():.3f}  accel(>1.1)={above1}/{len(va)}  decel(<0.9)={below1}/{len(va)}')

print()
print('=== delta_pressure at trigger: CONT vs MR ===')
for label, sub in [('CONT', cont), ('MR', rev)]:
    dp = sub['obs_delta_pressure_state'].value_counts(dropna=True)
    print(f'  {label}: {dict(dp)}')

print()
print('=== CONT zone_type distribution ===')
print(cont['zone_type'].value_counts())
print()
print('=== MR zone_type distribution ===')
print(rev['zone_type'].value_counts())
