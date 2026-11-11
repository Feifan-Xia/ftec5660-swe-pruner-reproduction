"""Question-level and repeat-level costs from the complete original-protocol subset."""
import json,statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];DEST=Path(__file__).parent/'figures';DEST.mkdir(exist_ok=True)
rows=json.loads((ROOT/'results/precision/cells.json').read_text(encoding='utf-8'));assert len(rows)==48 and all(r['qualified'] and r['score'] is not None for r in rows)
indices=json.loads((ROOT/'revision_precision/protocol.json').read_text(encoding='utf-8'))['question_indices']
fig,axes=plt.subplots(1,2,figsize=(7.2,3.0),layout='constrained',gridspec_kw={'width_ratios':[1.25,1]})
colors={'baseline':'#7a8790','pruner':'#246d7b'}
for j,i in enumerate(indices):
    values=[statistics.mean(r['total_tokens']/1000 for r in rows if r['index']==i and r['mode']==m) for m in colors]
    axes[0].plot(values,[j,j],color='#bdc4c9',zorder=1)
    for m,v in zip(colors,values):axes[0].scatter(v,j,color=colors[m],s=30,label=m if j==0 else None,zorder=2)
axes[0].set_yticks(range(8),[f'q{i}' for i in indices]);axes[0].invert_yaxis();axes[0].set_xscale('log');axes[0].set_xlabel('Mean tokens per task (K, log scale)',fontsize=9)
axes[0].set_title('(a) All eight fixed questions',loc='left',fontsize=10)
handles,labels=axes[0].get_legend_handles_labels();axes[0].legend(handles,['Full','Optional pruner'],fontsize=8,frameon=False)
for n,m in enumerate(colors):
    values=[statistics.mean(r['total_tokens']/1000 for r in rows if r['repeat']==rep and r['mode']==m) for rep in range(3)]
    x=[rep+(n-.5)*.32 for rep in range(3)];axes[1].bar(x,values,width=.30,color=colors[m],label=m)
    for pos,value in zip(x,values):axes[1].text(pos,value+2,f'{value:.1f}',ha='center',fontsize=8)
axes[1].set_xticks(range(3),['Repeat 1','Repeat 2','Repeat 3']);axes[1].set_ylim(0,185);axes[1].set_ylabel('Mean tokens per task (K)',fontsize=9);axes[1].set_title('(b) Complete paired repetitions',loc='left',fontsize=10)
for ax in axes:ax.spines[['top','right']].set_visible(False);ax.tick_params(labelsize=8)
for ext in ['png','pdf']:fig.savefig(DEST/f'precision.{ext}',dpi=240,bbox_inches='tight')
print('Saved complete fixed-subset cost figure.')
