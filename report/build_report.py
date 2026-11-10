"""Build a compact report from source plus measured formal results."""
import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, CondPageBreak
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--draft', action='store_true')
args = parser.parse_args()
source = (ROOT / 'report/report.md').read_text(encoding='utf-8')
analysis_path = ROOT / 'results/formal_analysis.json'
analysis = json.loads(analysis_path.read_text()) if analysis_path.exists() else None
if not args.draft and (not analysis or analysis['pending'] or not analysis.get('final')):
    raise RuntimeError('Final report requires complete formal evidence')

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyReport', fontName='Helvetica', fontSize=10.5, leading=14.5,
                         spaceAfter=8, splitLongWords=True))
styles['Title'].fontSize = 17
styles['Title'].leading = 21
styles['Heading1'].fontSize = 12
styles['Heading1'].spaceBefore = 11
styles['Heading2'].fontSize = 10.5
styles.add(ParagraphStyle(name='TableText', fontSize=8.5, leading=11))
styles.add(ParagraphStyle(name='TableCaption', parent=styles['BodyReport'], keepWithNext=True))
story = []

def fmt(value, pattern):
    return format(value, pattern) if value is not None else 'N/A'

def paragraph(text, style='BodyReport'):
    return Paragraph(escape(text), styles[style])

def table(rows):
    data = [[paragraph(str(v), 'TableText') for v in row] for row in rows]
    item = Table(data, hAlign='LEFT', repeatRows=1)
    item.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E8EEF5')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LINEBELOW', (0,0), (-1,0), .6, colors.HexColor('#52667B'))]))
    return KeepTogether([item])

def result_blocks():
    reference = json.loads((ROOT / 'configs/paper_reference.json').read_text())
    blocks = [paragraph('Published Streamlink reference (Table 2). Scores and tokens are averages per task. The original model and evaluation population differ from this reproduction.', 'TableCaption')]
    blocks.append(table([['Published model', 'Condition', 'Score', 'Tokens']] +
        [[r['model'], r['condition'], r['average_score'], f"{r['average_tokens']:,}"] for r in reference['rows']]))
    blocks.append(Spacer(1, 8))
    if not analysis:
        blocks.append(paragraph('DRAFT: Formal results are pending. Component checks below are measured; no formal comparison is claimed.'))
        return blocks
    rows = [['Local condition', 'Completed / tried', 'Mean tokens', 'Score', 'Pruned outputs', 'Expand calls']]
    for mode, r in analysis['conditions'].items():
        rows.append([mode, f"{r['completed']} / {r['attempted']}",
                     fmt(r['mean_tokens_all_attempts'], ',.0f'), fmt(r['mean_score_completed'], '.2f'),
                     r['pruned_observations'], r['recovery_reads']])
    blocks.append(table(rows))
    repeat_rows = [['Condition', 'Token mean SD across repeats', 'Score mean SD across repeats', 'Failure-zero score']]
    for mode, r in analysis['conditions'].items():
        repeat_rows.append([mode, fmt(r['repeat_token_mean_sample_sd'], ',.0f'),
                            fmt(r['repeat_score_mean_sample_sd'], '.3f'),
                            fmt(r['mean_score_failure_zero'], '.2f')])
    blocks.append(Spacer(1, 6))
    blocks.append(table(repeat_rows))
    cost_rows = [['Condition', 'Mean task elapsed time (s)', 'Provider list cost (USD)', 'Go allowance total', 'Conservative USD total']]
    for mode, r in analysis['conditions'].items():
        cost_rows.append([mode, fmt(r['mean_elapsed_seconds_all_attempts'], '.1f'),
                          fmt(r.get('provider_list_cost'), '.4f'),
                          fmt(r['go_allowance'], '.4f'), fmt(r['conservative_cost'], '.4f')])
    blocks.append(Spacer(1, 6))
    blocks.append(table(cost_rows))
    cash = sum(r['cash_cost'] for r in analysis['conditions'].values())
    blocks.append(paragraph(f'Agent-only cash charges recorded by the provider: ${cash:.4f}. These totals exclude judging and development; the full project ledger and evidence audit track the approved $8 ceiling.'))
    if not args.draft:
        audit = json.loads((ROOT / 'results/evidence_audit.json').read_text())
        repairs = json.loads((ROOT / 'results/judge_repairs.json').read_text())
        if audit['pending'] or audit['errors'] or repairs['unresolved']:
            raise RuntimeError('Final report requires resolved evidence audit and judge repairs')
        blocks.append(paragraph(f"Full-project conservative accounting, including development and judging: ${audit['project_conservative_usd']:.4f} against the approved ${audit['approved_limit_usd']:.2f} ceiling. {len(repairs['repaired'])} answers required the documented bounded judge-repair procedure; all original responses are retained."))
    for mode, r in analysis['conditions'].items():
        blocks.append(paragraph(f"{mode}: {r['timed_out_tool_calls']} shell-command timeouts; activated pruning processed {r['pruned_original_tokens']:,} source tokens and retained {r['pruned_kept_tokens']:,}. These source-token counts use the pruner tokenizer and are separate from cumulative agent API tokens."))
    blocks.append(paragraph('Token means include failed attempts. Score means cover completed, scored answers; failure-assigned and author-filtered summaries are supplied in formal_analysis.json.'))
    for name, comparison in analysis['paired'].items():
        ci = comparison['bootstrap_95_percentile']
        if ci is None:
            blocks.append(paragraph(f"{name.replace('_', ' ')}: complete three-repeat question pairs pending."))
            continue
        blocks.append(paragraph(f"{name.replace('_', ' ')}: paired mean token difference {comparison['mean_token_difference']:,.0f}; question-bootstrap 95% interval [{ci[0]:,.0f}, {ci[1]:,.0f}], {comparison['question_pairs']} question pairs."))
        score_ci = comparison['score_bootstrap_95_percentile']
        if score_ci is not None:
            blocks.append(paragraph(f"Failure-zero score sensitivity: paired difference {comparison['mean_failure_zero_score_difference']:.3f}; question-bootstrap 95% interval [{score_ci[0]:.3f}, {score_ci[1]:.3f}]."))
    figure = ROOT / 'results/formal_comparison.png'
    caption = paragraph('The uncertainty interval resamples question-level means, preserving the three repetitions within a question. The subset is small; these intervals describe this evaluation rather than population-wide effects.')
    if figure.exists():
        blocks.append(KeepTogether([Image(str(figure), width=480, height=192), caption]))
    else:
        blocks.append(caption)
    return blocks

for block in source.split('\n\n'):
    block = block.strip()
    if not block:
        continue
    if block == '{{RESULTS}}':
        story.extend(result_blocks())
    elif block == '{{CONCLUSIONS}}':
        conclusion = ROOT / 'results/conclusion.txt'
        if not args.draft and not conclusion.exists():
            raise RuntimeError('An evidence-reviewed conclusion is required for the final report')
        story.append(paragraph(conclusion.read_text(encoding='utf-8') if conclusion.exists() else 'DRAFT: Final interpretation will be written after the frozen formal schedule has been analyzed.'))
    elif block.startswith('### '):
        story.append(paragraph(block[4:], 'Heading2'))
    elif block.startswith('## '):
        if block.startswith('## 4.'):
            story.append(CondPageBreak(230))
        story.append(paragraph(block[3:], 'Heading1'))
    elif block.startswith('# '):
        story.append(paragraph(block[2:], 'Title'))
        if args.draft:
            story.append(paragraph('WORKING DRAFT — FORMAL RESULTS PENDING', 'Heading2'))
    else:
        story.append(paragraph(block.replace('\n', ' ')))

output = ROOT / 'report' / ('SWE-Pruner_report_draft.pdf' if args.draft else 'SWE-Pruner_report.pdf')
def footer(canvas, doc):
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#657080'))
    canvas.drawString(45, 24, 'FTEC5660 | SWE-Pruner reproduction' + (' | Draft' if args.draft else ''))
    canvas.drawRightString(A4[0]-45, 24, str(doc.page))
doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=45, leftMargin=45,
                        topMargin=40, bottomMargin=40,
                        title='SWE-Pruner reproduction with recoverable tool observations')
doc.build(story, onFirstPage=footer, onLaterPages=footer)
count = len(PdfReader(output).pages)
if count > 10:
    raise RuntimeError(f'Report exceeds ten pages: {count}')
print(f'{output}: {count} pages')
