"""Read accepted original snapshots; reconcile drawdown to every holding fragment.

No strategy execution, filtering, tuning, market fetch, or altered account.
Mechanical morphology labels are observations, not promoted causal roots.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/original_drawdown_trade_audit_v1'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2,
                                     allow_nan=False) + '\n')


def audit(frame, view, peak, trough):
    p = frame
    signs = p.exec_pos.to_numpy()
    splits = np.r_[0, np.flatnonzero(np.diff(signs)) + 1, len(p)]
    rows = []
    cumulative = 0.
    for trade, (a, b) in enumerate(zip(splits[:-1], splits[1:])):
        start, end = max(a, peak + 1), min(b, trough + 1)
        if start >= end:
            continue
        assert a > 1 and b < len(p), 'This diagnostic requires complete surrounding trades'
        q = p.iloc[start:end]
        direction = int(signs[start])
        path = np.r_[0., np.cumsum(q.pnl_log.to_numpy())]
        net = float(path[-1])
        mfe = float(path.max())
        giveback = mfe - net
        geometric = float(np.expm1(net) * 100)
        start_price = float(p.open.iloc[start - 1])
        end_price = float(p.open.iloc[end - 1])
        assert abs(direction * np.log(end_price / start_price) - net) < 1e-12
        cum_before = cumulative
        cumulative += net
        contribution = float(100 * (np.exp(cumulative) - np.exp(cum_before)))
        full_net = float(p.pnl_log.iloc[a:b].sum())
        raw_path = np.r_[0., np.cumsum(p.pnl_log.iloc[a:b].to_numpy())]
        overnight = 0.
        for i in range(start, end):
            if p.trading_day.iloc[i] != p.trading_day.iloc[i - 1]:
                overnight += direction * np.log(p.open.iloc[i] / p.close.iloc[i - 1])
        if net < 0 and mfe <= 1e-12:
            form = '窗口内未获顺向开盘浮盈'
        elif net < 0:
            form = '有顺向开盘浮盈但全部回吐并倒亏'
        else:
            form = '顺向开盘浮盈超过后续回吐'
        rows.append({
            'sequence': len(rows) + 1, 'global_trade': int(trade), 'direction': direction,
            'first_booking': str(q.timestamp.iloc[0]), 'last_booking': str(q.timestamp.iloc[-1]),
            'entry_signal_label': str(p.timestamp.iloc[a - 2]),
            'entry_fill_bar_label': str(p.timestamp.iloc[a - 1]),
            'exit_signal_label': str(p.timestamp.iloc[b - 2]),
            'exit_fill_bar_label': str(p.timestamp.iloc[b - 1]),
            'entry_price': float(p.open.iloc[a - 1]), 'exit_price': float(p.open.iloc[b - 1]),
            'fragment_start_price': start_price, 'fragment_end_price': end_price,
            'inherited_at_peak': bool(a < start), 'continues_after_trough': bool(b > end),
            'fragment_bars': int(end - start), 'full_trade_bars': int(b - a),
            'fragment_log_pnl': net, 'fragment_geometric_pct': geometric,
            'peak_nav_contribution_pp': contribution,
            'cumulative_drawdown_pct': float(100 * (1 - np.exp(cumulative))),
            'fragment_mfe_log_bp': mfe * 10000,
            'fragment_giveback_log_bp': giveback * 10000,
            'overnight_gap_log_bp': float(overnight * 10000),
            'full_trade_log_pnl': full_net,
            'full_trade_geometric_pct': float(100 * np.expm1(full_net)),
            'full_trade_mfe_log_bp': float(raw_path.max() * 10000),
            'entry_threshold_log_bp': float(p.threshold.iloc[a - 2] * 10000),
            'observed_shape_not_causal_verdict': form,
        })
    rows = pd.DataFrame(rows)
    expected = float(1 - p.nav.iloc[trough] / p.nav.iloc[peak]) * 100
    assert abs(rows.peak_nav_contribution_pp.sum() + expected) < 1e-10
    assert abs(rows.fragment_log_pnl.sum() - p.pnl_log.iloc[peak + 1:trough + 1].sum()) < 1e-12
    rows.to_csv(OUT / f'{view}_trades.csv', index=False, float_format='%.17g')
    means = []
    for label, group in [('loss', rows.loc[rows.fragment_log_pnl < 0]),
                         ('profit', rows.loc[rows.fragment_log_pnl > 0])]:
        means.append({'outcome': label, 'count': len(group),
            'net_log_sum': float(group.fragment_log_pnl.sum()),
            'mean_mfe_log_bp': float(group.fragment_mfe_log_bp.mean()),
            'mean_giveback_log_bp': float(group.fragment_giveback_log_bp.mean()),
            'mean_bars': float(group.fragment_bars.mean())})
    recovered = np.flatnonzero(p.nav.to_numpy()[trough + 1:] >= p.nav.iloc[peak])
    r = trough + 1 + int(recovered[0]) if len(recovered) else None
    result = {'view': view, 'peak': str(p.timestamp.iloc[peak]),
        'trough': str(p.timestamp.iloc[trough]),
        'recovery': str(p.timestamp.iloc[r]) if r is not None else None,
        'mdd_pct': expected, 'fragments': len(rows),
        'first_last_fragments_may_not_equal_completed_trades': True,
        'positive_log_sum': float(rows.loc[rows.fragment_log_pnl > 0, 'fragment_log_pnl'].sum()),
        'negative_log_sum': float(rows.loc[rows.fragment_log_pnl < 0, 'fragment_log_pnl'].sum()),
        'long_log_sum': float(rows.loc[rows.direction == 1, 'fragment_log_pnl'].sum()),
        'short_log_sum': float(rows.loc[rows.direction == -1, 'fragment_log_pnl'].sum()),
        'outcome_comparison': means,
        'accounting_reconciled': True,
        'phase_market_open_return_pct': float(100 * (p.open.iloc[trough] / p.open.iloc[peak] - 1)),
        'recovery_intervals': int(r - trough) if r is not None else None,
    }
    # A full per-fragment evidence table, without inventing per-trade root causes.
    lines = [f'# {view} 最大回撤逐笔记账证据', '',
        f'峰值行标签 {result["peak"]}；谷值行标签 {result["trough"]}；MDD {expected:.8f}%。', '',
        '原始多空满仓、零费signed-log指数账户不变。时间均为源K线结束标签，',
        '不是实际成交时钟；入场取所列fill bar的open。窗口边界只计窗内浮动损益。',
        '顺向空间与回吐来自持仓内开盘观察，不是完美可实现退出，也不是根因证明。', '',
        '|序号/原ID|窗内首末记账标签|方向|窗内log损益bp|MFE/回吐log bp|对峰值NAV贡献百分点|累计回撤%|边界与观察|',
        '|---|---|---|---:|---:|---:|---:|---|']
    for row in rows.itertuples():
        flags = ('峰时已有仓位；' if row.inherited_at_peak else '') + ('谷后仍持仓；' if row.continues_after_trough else '')
        lines.append(f'|{row.sequence}/{row.global_trade}|{row.first_booking} → {row.last_booking}|'
                     f'{"多" if row.direction == 1 else "空"}|{row.fragment_log_pnl * 10000:+.2f}|'
                     f'{row.fragment_mfe_log_bp:.2f}/{row.fragment_giveback_log_bp:.2f}|'
                     f'{row.peak_nav_contribution_pp:+.4f}|{row.cumulative_drawdown_pct:.4f}|'
                     f'{flags}{row.observed_shape_not_causal_verdict}|')
    (OUT / f'{view}_ledger.md').write_text('\n'.join(lines) + '\n')
    return result


def main():
    OUT.mkdir(exist_ok=True)
    save('data_usage.json', {'roles': {'2021-2025': 'repeat_audit_of_consumed_original_snapshots',
        '2026': 'excluded'}, 'policy_changes': 0, 'account_changes': 0,
        'purpose': 'drawdown trade accounting and observational morphology, not factor selection',
        'fresh_oos': False, 'production_authority': False})
    accepted = json.loads((ROOT / 'artifacts/streak_mechanism_v1/manifest.json').read_text())['files']
    summaries, inputs = [], {}
    for view in ['5m_offset_0', '5m_offset_2']:
        name = f'artifacts/streak_mechanism_v1/{view}/bars.parquet'
        inputs[name] = sha(ROOT / name)
        assert inputs[name] == accepted[name], name
        p = pd.read_parquet(ROOT / name)
        assert p.trading_day.max() <= '2025-12-31'
        assert np.allclose(p.nav, np.exp(p.pnl_log.cumsum()), rtol=1e-12, atol=1e-12)
        trough = int(np.argmin(p.drawdown.to_numpy()))
        peak = int(np.argmax(p.nav.to_numpy()[:trough + 1]))
        summaries.append(audit(p, view, peak, trough))
    save('summary.json', summaries)
    save('validation.json', {'accepted_input_hashes': inputs, 'accounting_passed': True,
        'source': str(Path(__file__).relative_to(ROOT)), 'source_sha256': sha(Path(__file__)),
        'output_hashes': {p.name: sha(p) for p in sorted(OUT.iterdir())
                          if p.is_file() and p.name != 'validation.json'},
        'manual_report_sha256': sha(ROOT / 'docs/research/original_drawdown_trade_audit_v1.md'),
        'new_backtest_calls': 0, 'per_trade_root_cause_complete': False})
    print(json.dumps(summaries, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
