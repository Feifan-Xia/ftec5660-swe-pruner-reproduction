"""Analyze the frozen formal inventory; retain failures and question-level pairing."""
import argparse
import json
from pathlib import Path
import statistics
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
MODES = ['baseline', 'pruner', 'recovery']

def mean(values):
    return statistics.mean(values) if values else None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-partial', action='store_true')
    args = parser.parse_args()
    rows = json.loads((ROOT / 'results/formal_tasks.json').read_text())
    schedule = json.loads((ROOT / 'runs/formal/schedule.json').read_text())
    key = lambda x: (x.get('question_index', x.get('index')), x['mode'], x['repeat'])
    lookup = {key(r): r for r in rows}
    pending = [job for job in schedule if key(job) not in lookup or lookup[key(job)]['status'] == 'running']
    if pending and not args.allow_partial:
        raise RuntimeError(f'{len(pending)} scheduled attempts unresolved; final analysis requires all attempts')
    if len(lookup) != len(rows) or set(lookup) - {key(x) for x in schedule}:
        raise ValueError('Duplicate or out-of-schedule formal result')
    summary = {'scheduled': len(schedule), 'pending': len(pending), 'conditions': {}, 'paired': {}}
    for mode in MODES:
        group = [r for r in rows if r['mode'] == mode and r['status'] != 'running']
        answered = [r for r in group if r['completed_answer']]
        scored = [r for r in answered if r['score'] is not None]
        if len(scored) != len(answered) and not args.allow_partial:
            raise RuntimeError(f'{mode}: completed answers have missing scores')
        repeats = []
        for repeat in range(3):
            part = [r for r in group if r['repeat'] == repeat]
            repeats.append({'repeat': repeat, 'tasks': len(part),
                            'mean_tokens': mean([r['total_tokens'] for r in part]),
                            'mean_scored_answer': mean([r['score'] for r in part if r['completed_answer'] and r['score'] is not None])})
        repeat_tokens = [r['mean_tokens'] for r in repeats if r['mean_tokens'] is not None]
        repeat_scores = [r['mean_scored_answer'] for r in repeats if r['mean_scored_answer'] is not None]
        summary['conditions'][mode] = {
            'attempted': len(group), 'completed': len(answered), 'scored': len(scored),
            'completion_rate': len(answered) / len(group) if group else None,
            'mean_tokens_all_attempts': mean([r['total_tokens'] for r in group]),
            'mean_input_tokens': mean([r['input_tokens'] for r in group]),
            'mean_output_tokens': mean([r['output_tokens'] for r in group]),
            'mean_score_completed': mean([r['score'] for r in scored]),
            'mean_score_failure_zero': mean([r['score'] if r in scored else 0 for r in group]),
            'mean_seconds_completed': mean([r['seconds'] for r in answered if r['seconds'] is not None]),
            'author_filtered_score': mean([r['score'] for r in scored if r['author_filtered_eligible']]),
            'author_filtered_n': sum(r['author_filtered_eligible'] is True for r in scored),
            'pruned_observations': sum(r['pruned_observations'] for r in group),
            'tasks_with_pruning': sum(r['pruned_observations'] > 0 for r in group),
            'timed_out_tool_calls': sum(r.get('timed_out_tool_calls', 0) for r in group),
            'pruned_original_tokens': sum(r.get('pruned_original_tokens', 0) for r in group),
            'pruned_kept_tokens': sum(r.get('pruned_kept_tokens', 0) for r in group),
            'recovery_reads': sum(r['recovery_reads'] for r in group),
            'cash_cost': sum(r['cash_cost'] for r in group),
            'go_allowance': sum(r['go_allowance'] for r in group),
            'conservative_cost': sum(r['conservative_cost'] for r in group),
            'repeat_token_mean_sample_sd': statistics.stdev(repeat_tokens) if len(repeat_tokens) > 1 else None,
            'repeat_score_mean_sample_sd': statistics.stdev(repeat_scores) if len(repeat_scores) > 1 else None,
            'repeats': repeats}
    rng = random.Random(5660)
    for comparison, control in [('pruner', 'baseline'), ('recovery', 'pruner')]:
        differences = []
        score_differences = []
        for question in sorted({r['question_index'] for r in rows}):
            groups = [[r for r in rows if r['question_index'] == question and r['mode'] == m and r['status'] != 'running']
                      for m in (comparison, control)]
            if all(len(g) == 3 for g in groups):
                differences.append(mean([r['total_tokens'] for r in groups[0]]) - mean([r['total_tokens'] for r in groups[1]]))
                if all(not r['completed_answer'] or r['score'] is not None for group in groups for r in group):
                    score_differences.append(mean([r['score'] if r['completed_answer'] else 0 for r in groups[0]])
                                             - mean([r['score'] if r['completed_answer'] else 0 for r in groups[1]]))
        samples = sorted(mean(rng.choices(differences, k=len(differences))) for _ in range(5000)) if differences else []
        score_samples = sorted(mean(rng.choices(score_differences, k=len(score_differences))) for _ in range(5000)) if score_differences else []
        summary['paired'][f'{comparison}_minus_{control}'] = {
            'question_pairs': len(differences), 'mean_token_difference': mean(differences),
            'bootstrap_95_percentile': [samples[124], samples[4874]] if samples else None,
            'question_differences': differences,
            'mean_failure_zero_score_difference': mean(score_differences),
            'score_bootstrap_95_percentile': [score_samples[124], score_samples[4874]] if score_samples else None}
    (ROOT / 'results/formal_analysis.json').write_text(json.dumps(summary, indent=2))
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), layout='constrained')
    colors = ['#426B9E', '#299A83', '#CC8A35']
    axes[0].bar(MODES, [summary['conditions'][m]['mean_tokens_all_attempts'] or 0 for m in MODES], color=colors)
    axes[0].set_ylabel('Mean cumulative tokens / attempted task')
    axes[0].ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
    axes[1].bar(MODES, [summary['conditions'][m]['mean_score_completed'] or 0 for m in MODES], color=colors)
    axes[1].set_ylabel('Mean rubric score / scored answer')
    axes[1].set_ylim(0, 10)
    for ax in axes:
        ax.spines[['top', 'right']].set_visible(False)
    fig.savefig(ROOT / 'results/formal_comparison.png', dpi=180)
    fig.savefig(ROOT / 'results/formal_comparison.pdf')
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
