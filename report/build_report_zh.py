"""Build the Chinese report from translated prose and frozen measured results."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, CondPageBreak
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
FONT = Path('C:/Windows/Fonts/msyh.ttc')
BOLD = Path('C:/Windows/Fonts/msyhbd.ttc')
pdfmetrics.registerFont(TTFont('Chinese', str(FONT)))
pdfmetrics.registerFont(TTFont('ChineseBold', str(BOLD)))
analysis = json.loads((ROOT/'results/formal_analysis.json').read_text())
audit = json.loads((ROOT/'results/evidence_audit.json').read_text())
assert analysis['final'] and not analysis['pending'] and not audit['errors'] and not audit['pending']
names = {'baseline':'完整输出（baseline）', 'pruner':'剪枝（pruner）', 'recovery':'剪枝＋恢复（recovery）'}
short = {'baseline':'完整输出', 'pruner':'剪枝', 'recovery':'剪枝＋恢复'}

def md_table(header, rows):
    return '\n'.join(['| '+' | '.join(header)+' |', '| '+' | '.join(['---']*len(header))+' |']+
                     ['| '+' | '.join(map(str,row))+' |' for row in rows])

sections = ['论文 Streamlink 参考结果（表 2）。分数和 tokens 均为每题平均值；论文模型及评测范围与本次实验存在差异。']
reference = json.loads((ROOT/'configs/paper_reference.json').read_text())
sections.append(md_table(['论文模型','条件','平均分','平均 tokens'],
    [[r['model'],r['condition'],f"{r['average_score']:.2f}",f"{r['average_tokens']:,}"] for r in reference['rows']]))
c = analysis['conditions']
sections.append('本地三组结果。token 均值包含全部尝试，回答均分使用有效导出且已评分的答案。')
sections.append(md_table(['条件','有效／尝试','平均 tokens','回答均分','剪枝次数','恢复次数'],
    [[short[m],f"{r['completed']}/{r['attempted']}",f"{r['mean_tokens_all_attempts']:,.0f}",f"{r['mean_score_completed']:.2f}",r['pruned_observations'],r['recovery_reads']] for m,r in c.items()]))
sections.append(md_table(['条件','重复均值的 token 标准差','重复均值的评分标准差','失败记零均分'],
    [[short[m],f"{r['repeat_token_mean_sample_sd']:,.0f}",f"{r['repeat_score_mean_sample_sd']:.3f}",f"{r['mean_score_failure_zero']:.2f}"] for m,r in c.items()]))
sections.append('下表为 Agent 正式运行的耗时与费用，开发、调试和评分开销单独计入项目总账。')
sections.append(md_table(['条件','平均整题耗时（秒）','list cost（美元）','Go 额度','保守计数（美元）'],
    [[short[m],f"{r['mean_elapsed_seconds_all_attempts']:.1f}",f"{r['provider_list_cost']:.4f}",f"{r['go_allowance']:.4f}",f"{r['conservative_cost']:.4f}"] for m,r in c.items()]))
provider = audit['provider_recorded_usage']
sections.append(f"保存的全项目服务商 usage 合计 list cost 为 ${provider['list_cost_usd']:.4f}，Go 额度消耗为 {provider['go_allowance']:.4f}，现金收费为 ${provider['cash_cost_usd']:.4f}。保守预算计数为 ${audit['project_conservative_usd']:.4f}，批准上限为 $8。总账包含开发与评分；最初未保存完整 usage 的连通性探针仅计入保守预算。核查时 list cost 与平台 Cost 显示口径对齐。")
sections.append('累计 API tokens 包含缓存命中的输入；保守预算将全部输入按未缓存峰值价格计入。3 份截断评分已完成补充，初始响应全部保留。')
sections.append(md_table(['条件','发生剪枝的任务数','命令超时次数','剪枝输入 tokens','剪后保留 tokens'],
    [[short[m],r['tasks_with_pruning'],r['timed_out_tool_calls'],f"{r['pruned_original_tokens']:,}",f"{r['pruned_kept_tokens']:,}"] for m,r in c.items()]))
sections.append('剪枝输入与保留量由剪枝模型的 tokenizer 统计；累计 Agent API tokens 则由服务商 usage 统计，两者对应不同的测量对象。作者的过滤后评分及失败记零统计保存在 formal_analysis.json。')
for key,label in [('pruner_minus_baseline','剪枝相对完整输出'),('recovery_minus_pruner','剪枝＋恢复相对剪枝')]:
    r=analysis['paired'][key]; lo,hi=r['bootstrap_95_percentile']; sl,sh=r['score_bootstrap_95_percentile']
    sections.append(f"{label}：配对平均 token 差为 {r['mean_token_difference']:,.0f}，题目层面的 bootstrap 95% 区间为 [{lo:,.0f}, {hi:,.0f}]，共 {r['question_pairs']} 对题目。失败记零评分的配对差为 {r['mean_failure_zero_score_difference']:.3f}，对应区间为 [{sl:.3f}, {sh:.3f}]。")
sections.extend(['![三组结果对比](../results/formal_comparison_zh.png)', '图 1：三组累计 token 与有效答案均分。上述区间在题目层面重采样，每题内保留三次重复的平均值。小子集区间描述本次评测的不确定性，推广到更广泛任务需要更多数据。'])
source=(ROOT/'report/report_zh_source.md').read_text(encoding='utf-8').replace('{{RESULTS}}','\n\n'.join(sections))
(ROOT/'report/report_zh.md').write_text(source,encoding='utf-8')

font=FontProperties(fname=str(FONT))
fig,axes=plt.subplots(1,2,figsize=(9,3.6),layout='constrained')
labels=list(short.values()); palette=['#426B9E','#299A83','#CC8A35']
for ax,metric,ylabel in [(axes[0],'mean_tokens_all_attempts','每次尝试的平均累计 API tokens'),(axes[1],'mean_score_completed','有效答案平均评分')]:
    ax.bar(labels,[r[metric] for r in c.values()],color=palette)
    ax.set_ylabel(ylabel,fontproperties=font)
    for label in ax.get_xticklabels(): label.set_fontproperties(font)
    ax.spines[['top','right']].set_visible(False)
axes[1].set_ylim(0,10)
fig.savefig(ROOT/'results/formal_comparison_zh.png',dpi=180)
plt.close(fig)

styles = {
    'body':ParagraphStyle('body',fontName='Chinese',fontSize=10.5,leading=17,spaceAfter=8,wordWrap='CJK'),
    'title':ParagraphStyle('title',fontName='ChineseBold',fontSize=18,leading=25,spaceAfter=10,alignment=1,wordWrap='CJK'),
    'h1':ParagraphStyle('h1',fontName='ChineseBold',fontSize=13,leading=20,spaceBefore=12,spaceAfter=8,keepWithNext=True,wordWrap='CJK'),
    'h2':ParagraphStyle('h2',fontName='ChineseBold',fontSize=11,leading=17,spaceBefore=8,spaceAfter=6,keepWithNext=True,wordWrap='CJK'),
    'table':ParagraphStyle('table',fontName='Chinese',fontSize=9,leading=14,wordWrap='CJK'),
}
def para(t,style='body'): return Paragraph(escape(t),styles[style])
story=[]
for block in source.split('\n\n'):
    block=block.strip()
    if not block: continue
    if block.startswith('|'):
        rows=[[v.strip() for v in line.strip('|').split('|')] for line in block.splitlines() if not line.startswith('| ---')]
        width=(A4[0]-90)/len(rows[0])
        table=Table([[para(x,'table') for x in row] for row in rows],colWidths=[width]*len(rows[0]),repeatRows=1)
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E8EEF5')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#52667B'))]))
        story.extend([KeepTogether([table]),Spacer(1,8)])
    elif block.startswith('!['):
        story.append(Image(str(ROOT/'results/formal_comparison_zh.png'),width=490,height=196))
    elif block.startswith('### '): story.append(para(block[4:],'h2'))
    elif block.startswith('## '):
        if block.startswith('## 4.'): story.append(CondPageBreak(240))
        story.append(para(block[3:],'h1'))
    elif block.startswith('# '):
        for line in block.splitlines(): story.append(para(line.removeprefix('# '),'title'))
    else: story.append(para(block.replace('\n',' ')))

output=ROOT/'report/SWE-Pruner_report_zh.pdf'
def footer(canvas,doc):
    canvas.setFont('Chinese',8); canvas.setFillColor(colors.HexColor('#657080'))
    canvas.drawString(45,24,'FTEC5660｜SWE-Pruner 复现报告｜中文版')
    canvas.drawRightString(A4[0]-45,24,str(doc.page))
doc=SimpleDocTemplate(str(output),pagesize=A4,leftMargin=45,rightMargin=45,topMargin=40,bottomMargin=42,title='SWE-Pruner 在 SWE-QA 上的复现：可恢复工具观测',author='Xia Feifan')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
count=len(PdfReader(output).pages)
assert count<=10,count
print(f'{output}: {count} pages')
