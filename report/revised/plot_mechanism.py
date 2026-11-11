"""Publication figure from the completed 72-cell corrected mechanism study."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];DEST=Path(__file__).parent/'figures';DEST.mkdir(exist_ok=True)
r=json.loads((ROOT/'results/recovery/mechanism.json').read_text(encoding='utf-8'));assert r['final'] and r['n']==72
groups=r['conditions'];modes=['full','pruned','recoverable'];colors=['#81919c','#b67d43','#216a77']
fig,axes=plt.subplots(1,2,figsize=(7.2,2.5),layout='constrained')
for axis,values,title,ylabel in [(axes[0],[100*groups[m]['correct']/groups[m]['n'] for m in modes],'(a) Exact-match success','SR (%)'),(axes[1],[(groups[m]['input_tokens']+groups[m]['output_tokens'])/groups[m]['n'] for m in modes],'(b) Follow-up API tokens','Mean cumulative tokens')]:
    axis.bar(['Full','Pruned','Recoverable'],values,color=colors,width=.58)
    axis.set_title(title,fontsize=10,loc='left');axis.set_ylabel(ylabel,fontsize=9);axis.tick_params(labelsize=8)
    axis.spines[['top','right']].set_visible(False);axis.set_ylim(0,max(values)*1.2)
    for i,v in enumerate(values):axis.text(i,v+max(values)*.025,f'{v:.1f}%' if axis is axes[0] else f'{v:,.0f}',ha='center',fontsize=9)
axes[0].set_ylim(0,112)
axes[0].set_yticks([0,25,50,75,100])
for extension in ['png','pdf']:fig.savefig(DEST/f'mechanism.{extension}',dpi=240,bbox_inches='tight')
print('Saved measured mechanism figure; 8 cases x 3 repeats per condition.')
