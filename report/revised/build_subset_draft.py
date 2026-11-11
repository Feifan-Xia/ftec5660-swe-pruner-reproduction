"""Build the evidence-backed subset manuscript while full-population work continues."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
e=read('results/full/manuscript_evidence.json');g=e['groups'];c=e['comparisons']
def ci(name,metric):return '、'.join(f'{v:+.1f}%' for v in c[name][metric]['ci95_percent'])
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(str(x) for x in r)+' |' for r in rows])
def row(label,key,note):
    r=g[key];return [label,str(r['n']),f"{r['score']:.2f}",f"{r['tokens']/1000:.1f}",f"{r['rounds']:.1f}",note]
values={
'ABSTRACT_RESULTS':'固定八题、每组重复三次的 48 项问答全部完成。修复执行目录、步数、padding 与参数加载精度后，原始可选提示协议的累计 tokens 降低 17.6%，评分提高 1.3%；三个重复的 token 方向一致，问题 cluster 区间跨零，剪枝触发覆盖率为 25.0%。',
'ABSTRACT_MODIFICATION':'在强制触发诊断中，恢复相对剪枝降低 11.6% tokens、提高 1.4% 评分；在固定证据目标变化实验中，精确匹配 SR 从 12.5% 提升至 100.0%，累计 tokens 增加 196.4%。原始可选提示下的恢复三重复正在完成，以检验该修改在原协议中的实际收益。',
'INTRO_REPRODUCTION':'修正后原协议得到 136.4K → 112.3K tokens（−17.6%）和 9.00 → 9.12 评分（+1.3%）。相比旧配置的 +16.1% tokens，端到端方向恢复为下降；平均降幅与作者相同八题记录的 −49.9% 仍有差距，低触发覆盖率也限制了对剪枝机制的归因。',
'INTRO_MODIFICATION':'在必填 hint 的八题诊断中，恢复使调用次数减少 22.4%、累计 tokens 减少 11.6%、评分提高 1.4%；受控目标变化实验的 SR 提升 87.5 个百分点，代价为 196.4% 更多 tokens。原始可选 hint 下的完整三重复用于补充其正常工作负载收益。',
'AUTHOR_TABLE':table(['仓库与来源','full tokens K','pruner tokens K','变化','full/pruner 评分'],[
 ['Streamlink，论文表 2','318.2','145.1','−54.4%','8.56 / 8.56'],
 ['Streamlink，作者公开运行记录','142.3','101.2','−28.9%','8.56 / 8.56'],
 ['Reflex，论文表 2','142.3','101.2','−28.9%','8.37 / 8.23'],
 ['Reflex，作者公开运行记录','318.2','145.1','−54.4%','8.37 / 8.23']])+'\n\n表 1. GLM-4.6 的论文与发布产物对照。tokens 为每题平均 input+output；产物评分采用作者配对过滤规则。两仓库 token 对应的交叉关系可由原始文件复算。',
'STUDY_SCOPE':'本阶段固定使用初始选定的 Streamlink 八题，零基题号为 41、14、30、8、11、46、33、29。原始 full 与 optional-hint pruner 各三次，共 48 项；必填 hint 的完整输出、剪枝、恢复各八项，共 24 项。另有固定观测的 72 项机制实验，以及原始 optional-hint recovery 的 24 项独立重复。全部 48 题扩展的范围与费用已单独记录，当前稿展示已完成的 subset 证据。',
'SETTINGS_TABLE':table(['项目','配置'],[
 ['Agent 与路由','GLM-4.6；OpenRouter 固定 Z.AI，fallback 关闭'],
 ['评分','GPT-5；作者五维 JSON rubric；固定 OpenAI 路由'],
 ['生成','temperature 0，top_p 1，max output 16,384；终止摘要 temperature 0.3'],
 ['执行限额','50 次交互；每题 1,800 秒；三仓库共享根目录'],
 ['Pruner','发布 checkpoint；FP32 参数、FP16 autocast；阈值 0.5；8192 padding'],
 ['运行环境','Windows 11 / WSL Ubuntu 22.04；Python 3.12；OpenHands SDK 1.1.0'],
 ['数值环境','PyTorch 2.9.0.dev20250705+cu129；Transformers 4.57.1；8GB GPU'],
 ['修改接口','每任务原始文本存储；内容哈希 ID；每次 expand 最多 200 行']])+'\n\n表 2. 共同实验配置。作者原始模型网关和服务细节差异在第 3 节说明。',
'MAIN_TABLE':table(['来源与条件','执行项','评分 / 10','tokens K','轮数','说明'],[
 ['论文 Streamlink full','48','8.56','318.2','18.2','原表 2'],
 ['论文 Streamlink pruner','48','8.56','145.1','25.0','−54.4% tokens'],
 ['作者记录 full','48','8.56','142.3','18.2','43 题评分'],
 ['作者记录 pruner','48','8.56','101.2','25.0','−28.9% tokens'],
 ['作者记录，相同八题 full','8','8.25','190.2','—','每题一次，全部评分'],
 ['作者记录，相同八题 pruner','8','8.60','95.3','—','−49.9% tokens'],
 row('本地 full','original_full','八题 × 三次'),row('本地 pruner','original_pruner','−17.6% tokens'),
 row('本地 full，终止修复','repaired_full','同前缀重放一项'),row('本地 pruner，终止修复','original_pruner','−18.0% tokens')])+'\n\n表 3. 原文、作者公开运行记录与本地原协议统一对照。所有 tokens 使用 K=1000。论文与产物评分按其过滤分母，本地保留全部 24 项；终止修复行只替换受影响的终止调用，原始实验完整保留。',
'MAIN_RESULT_ANALYSIS':'原协议本地三次重复的 token 变化分别为 −27.7%、−16.0%、−10.4%，平均为 −17.6%；评分相对增加 1.3%。终止序列化修复后，full 均值为 137.0K 和 9.04，pruner 保持 112.3K 和 9.12，得到 −18.0% tokens 和 +0.8% 评分。作者公开运行记录中的相同八题的 tokens 为 190.2K → 95.3K（−49.9%）；因此任务范围对齐后，本地仍未达到作者记录的下降幅度。表 3 的全仓库参考与同题参考分别刻画了总体对照和样本对照。相同八题的每题绝对节省由作者 94.9K 缩小为本地 24.0K，差额 70.9K 中约 76.0% 来自本地 full 用量较低，24.0% 来自本地 pruner 用量较高。例如 q29 的 full 为作者 217.8K、本地 40.7K，pruner 为作者 68.5K、本地 66.3K。该算术分解说明 full 调查路径差异对节省比例有重要影响；模型服务和路径选择各自的因果贡献仍需独立控制。',
'UNCERTAINTY_ANALYSIS':f"原协议 token 相对变化的 95% 问题 cluster 区间为 [{ci('original','total_tokens')}]，评分变化区间为 [{ci('original','score')}]。区间跨零反映八个问题之间的显著异质性；三次重复增加了路径观察次数，独立问题数仍为八。本文结论为该 subset 的平均节省方向得到重现，降幅及机制覆盖仍有偏差。全题扩展将检验这种方向能否覆盖其余问题。\n\n![图 1. 固定八题的题均累计 tokens 与三次重复的组均值。每个问题和重复均保留，长路径对总体的影响可直接观察。](figures/precision.png)",
'ACTIVATION_TABLE':table(['配置','触发覆盖','平均请求数','tokens K','质量变化'],[
 ['作者 Streamlink pruner','100.0%','未提供同口径','101.2','0.0%'],
 ['本地 optional pruner','25.0%','10.46','112.3','+1.3% vs full'],
 ['必填 hint 完整输出','0.0%','10.13','134.1','对照'],
 ['必填 hint 剪枝','100.0%','20.13','177.6','−1.3% vs 匹配 full'],
 ['必填 hint 剪枝，终止修复','100.0%','20.13','178.9','−0.3% vs 匹配 full']])+'\n\n表 4. 触发覆盖与调查路径。覆盖率分母为任务数；必填 hint 三组各八题一次，属于独立机制诊断。',
'TRAJECTORY_ANALYSIS':'optional 组实际送入 skimmer 的 199,487 tokens 压缩至 37,030，压缩率为 81.4%，仅六次调用。必填 hint 组压缩率为 68.3%，每请求 tokens 降低 33.3%，请求数却增加 98.8%，使整项任务 tokens 增加 32.5%。这给出明确的成本分解：更短的单次上下文，被更多次检索和历史重复发送抵消。q33 的强制剪枝轨迹反复以 cat、sed、Python、grep、awk 读取同一测试文件；多次超过千 tokens 的输出仅留下七 tokens，模型随后改用更短的行范围。原工具说明允许省略 hint 获取重要细节，必填约束关闭了这一重读路径。q29 也出现反复读取同一 CDP 生成文件的过程。',
'MODIFICATION_TABLE':table(['诊断条件','执行项','评分 / 10','tokens K','请求数','恢复覆盖'],[
 ['必填剪枝','8','9.20','177.6','20.13','0.0%'],
 ['必填剪枝，终止修复','8','9.30','178.9','20.13','0.0%'],
 ['必填剪枝 + 恢复','8','9.33','156.9','15.63','62.5%']])+'\n\n表 5. 恢复修改的必填 hint 诊断。相对原终止行为为 −11.6% tokens、+1.4% 评分；相对修复后的剪枝为 −12.3% tokens、+0.3% 评分。',
'MODIFICATION_ANALYSIS':f"八题恢复组全部在首轮完成，五题使用恢复。21 次成功 expand 均逐字符匹配对应原始切片，并暴露此前未显示的非空文本；共返回 68,749 字符，重复读取 17 行。相对修复后的必填剪枝，token 变化区间为 [{ci('required_recovery_repaired','total_tokens')}]，评分变化区间为 [{ci('required_recovery_repaired','score')}]。这一诊断支持恢复可缓解部分反复过滤路径，平均质量的变化较小且存在明显不确定性。原始 optional-hint 配置的 24 项恢复对照将在全部完成后写入同一主表。\n\n![图 2. 原始数值配置下的固定证据目标变化实验，三组各 24 项。左图为精确匹配 SR，右图为累计 API tokens。](figures/mechanism.png)",
'LIMITATIONS':'任务范围覆盖 Streamlink 中预先固定的八题，问题簇较少；全题结果将在扩展完成后更新。作者与本地模型服务、评分服务和未公开辅助文件存在差异。三重复温度为零仍出现不同工具路径，API 内部确定性无法控制。不同阶段顺序执行，GPU 串行服务和网络中断使运行时间受排队与恢复影响，因此 latency 作为运行记录呈现。LLM 五维评分能够核对参考答案覆盖与解释质量，其小幅差异仍需结合答案文本审阅；未预设的通过阈值不会用于构造 QA 成功率。',
'DEBUG_TABLE':table(['发现','证据','处理与影响'],[
 ['目录、步数偏差','作者配置与本地启动参数','恢复共享根目录与 50 步'],
 ['Padding 与加载精度','固定输入精确输出匹配 5/8 → 7/8','恢复 8192 padding 与 FP32 参数'],
 ['Token 累加重复','72/72 重放为独立账本两倍','累计与逐调用分支互斥'],
 ['终止分支丢失工具内容','真实对象 content=[]；两条轨迹命中','使用实际可见内容，保留同前缀重放'],
 ['剪枝低触发','原协议六次；必填组 148 次','原协议保留，另做匹配策略诊断'],
 ['网络中断与缺失回执','同步连接重置、DNS/SSL 错误','保存失败，按基础设施条件恢复与核账']])+'\n\n表 6. 可定位偏差与处理链。多个配置同时修正后的总体差异用于版本比较，单项影响以固定输入或明确对照支持。',
'COMPLETENESS_COST':'原协议 48 项的最终执行完成率为 100.0%，首轮完成率为 79.2%；所有选定执行都有完整 transmitted-request usage。必填 hint 的三组共 24 项与机制 72 项均完成。网络切换曾引发多个连接同时重置，失败调用与估计上限均保留。预算使用独立逐请求账本，并用服务商回执核对已结算费用；Go 套餐记录成本与现金收费分别记录。本文表中 tokens 对应选定完整执行，全部尝试的实际费用及未知费用上界另列于账本。',
'CONCLUSION':'在配置与计量修复后，固定 Streamlink 八题的原协议 GLM-4.6 复现得到平均 17.6% tokens 节省和 1.3% 评分增加，三轮 token 方向一致。作者公开运行记录的 token 仓库对应、实际 hint 触发与终止证据序列化分别解释了参考值、机制执行和最终答案的关键差异。任务级原始观测恢复在强制剪枝诊断中减少平均请求数与 tokens，在固定证据目标变化实验中把 SR 从 12.5% 提升到 100.0%，并显示显著的交互代价。原协议恢复重复和全题扩展将进一步确定其正常工作负载效果及总体适用范围。'
}
if 'optional_recovery' in g:
    r=g['optional_recovery'];effect=c['optional_recovery']
    assert r['n']==24
    values['ABSTRACT_MODIFICATION']='在原协议下，该修改使平均评分提高 1.4%、累计 tokens 增加 11.3%；质量变化区间跨零。固定证据目标变化实验的精确匹配 SR 从 12.5% 提升至 100.0%，累计 tokens 增加 196.4%。'
    values['INTRO_MODIFICATION']='原协议八题三重复结果显示，该修改相对 SWE-Pruner 提高平均评分 1.4%，代价为 11.3% 更多 tokens。12 次成功恢复均返回此前未显示的原始文本，恢复覆盖 12.5% 的任务。受控目标变化实验的 SR 提升 87.5 个百分点，伴随 196.4% 更多 tokens；这些结果把精确取回的能力与完整 Agent 的成本权衡连接起来。'
    values['STUDY_SCOPE']=values['STUDY_SCOPE'].replace('另有固定观测的 72 项机制实验，以及原始 optional-hint recovery 的 24 项独立重复。','原始 optional-hint recovery 的 24 项独立重复与原协议对照合计 72 项，全部完成；另有固定观测的 72 项机制实验。')
    values['MAIN_TABLE']=values['MAIN_TABLE'].replace('\n\n表 3.',f"\n| 本地 pruner + 恢复 | 24 | {r['score']:.2f} | {r['tokens']/1000:.1f} | {r['rounds']:.1f} | 原始可选 hint |\n\n表 3.")
    values['MODIFICATION_TABLE']=table(['协议与条件','执行项','评分 / 10','tokens K','请求数','恢复覆盖'],[
        ['可选提示：pruner','24','9.12','112.3','10.46','0.0%'],
        ['可选提示：pruner + 恢复','24','9.24','125.1','11.08','12.5%'],
        ['必填提示：剪枝','8','9.20','177.6','20.13','0.0%'],
        ['必填提示：剪枝，终止修复','8','9.30','178.9','20.13','0.0%'],
        ['必填提示：剪枝 + 恢复','8','9.33','156.9','15.63','62.5%']])+'\n\n表 5. 同一协议内的恢复修改对照。原始可选提示为三重复主比较；必填提示为单重复诊断。所有任务均有完整用量与评分。'
    values['MODIFICATION_ANALYSIS']=f"原协议恢复组平均质量为 9.24，相对 pruner 的 9.12 提高 1.4%，95% 问题 cluster 区间为 [{ci('optional_recovery','score')}]；tokens 从 112.3K 增至 125.1K（+11.3%），区间为 [{ci('optional_recovery','total_tokens')}]，请求数增加 6.0%。由此观察到较明确的 token 代价和不确定的小幅质量收益。恢复在三项任务中被使用，共 12 次成功读取、51,480 返回字符和两行重复读取，均逐字符匹配原始切片，并提供新的非空文本。另有七次请求超过 200 行上限、两次范围越界，均返回错误提示；这些失败计入实际回合与 tokens，说明行范围选择仍有接口使用成本。\n\n必填提示诊断的八题恢复组全部在首轮完成，五题使用恢复。21 次成功读取均暴露此前未显示的非空文本，共返回 68,749 字符，重复读取 17 行。相对修复后的必填剪枝，tokens 降低 12.3%、评分提高 0.3%；区间分别为 [{ci('required_recovery_repaired','total_tokens')}] 和 [{ci('required_recovery_repaired','score')}]。强制过滤增加了重复检索，恢复在这一场景的作用更大；原始可选提示保留 Bash 直接重读路径，额外恢复工具的平均代价更明显。两组独立路径和较少问题簇限制了因果精度。\n\n![图 2. 发布数值配置下的固定证据目标变化实验，三组各 24 项。左图为精确匹配 SR，右图为累计 API tokens。](figures/mechanism.png)"
    values['COMPLETENESS_COST']='原始可选提示下三组共 72 项的最终执行完成率为 100.0%，首轮完成率为 81.9%；原协议 full/pruner 的 48 项为 79.2%，恢复 24 项为 87.5%。所有选定执行都有完整 transmitted-request usage。必填提示诊断 24 项与机制 72 项也全部完成。网络切换引发的连接重置、DNS/SSL 故障与缺失回执均保留；一个并发续评造成的重复评分按预先规定保留最早有效响应，两次响应和费用均可查。新续评入口加入同题互斥锁和精确 cell 定位。项目保守账本累计约 $9.69，批准上限为 $12；全题扩展的预算仍待确认。表中 tokens 对应选定完整执行，全部尝试费用及未知上界另列于账本。'
    values['CONCLUSION']='在配置与计量修复后，固定 Streamlink 八题的原协议 GLM-4.6 复现得到平均 17.6% tokens 节省和 1.3% 评分增加，三轮 token 方向一致。相同八题的作者公开运行记录节省 49.9%，差距同时涉及 full 调查路径和 pruner 行为，当前属于方向一致、幅度与机制覆盖仍有偏差的部分复现。新增任务级原始观测恢复在原协议下提高平均评分 1.4%、增加 tokens 11.3%；质量收益仍有不确定性。受控目标变化实验把 SR 从 12.5% 提升到 100.0%，伴随显著额外成本。完整问答、机制实验与失败轨迹共同界定了该修改的功能、收益与代价；全题扩展将继续检验总体适用范围。'
from gap_sections import ZH_FIDELITY, ZH_TRAJECTORY, ZH_DEVELOPMENT
values['ABSTRACT_RESULTS'] += '作者同一八题的累计 tokens 下降 49.9%。全部 131 条作者观测重放得到 96.9% 逐字匹配，压缩率为本地 81.12%、作者 81.11%；剩余差距集中于 hint 使用与搜索路径。'
values['INTRO_REPRODUCTION'] += '同一输入下的剪枝器压缩率已高度一致；本地 Bash hint 使用率为 2.4%，作者为 100%，作者 full 还包含九次命令超时。'
values['CONCLUSION'] = values['CONCLUSION'].replace('全题扩展将继续检验总体适用范围。','当前优先在固定小范围内验证策略对齐，再评估扩展。')
text=(HERE/'template_zh.md').read_text(encoding='utf-8')
text=text.replace('### 3.3 Token 账本验证', ZH_FIDELITY+'\n\n### 3.3 Token 账本验证')
start=text.index('固定八题首轮配置修复后的'); end=text.index('\n\n### 5.3',start)
text=text[:start]+ZH_TRAJECTORY+text[end:]
for key,value in values.items():text=text.replace('{{'+key+'}}',value)
assert not re.search(r'\{\{.*?\}\}',text)
assert all('?' not in line and '？' not in line for line in text.splitlines() if line.startswith('#'))
text=text.replace('FTEC5660 Individual Reproducibility Project · 2026 年 11 月','FTEC5660 Individual Reproducibility Project · 2026 年 11 月\n\n固定 subset 验证稿 · 小范围对齐诊断')
text=text.replace('## 6. 讨论与可复查性',ZH_DEVELOPMENT+'## 6. 讨论与可复查性')
text=text.replace('项目保守账本累计约 $9.69，批准上限为 $12；全题扩展的预算仍待确认。','纳入本轮诊断并按账户用量去除重复预留后，项目保守累计约 $9.47，批准上限为 $12；全题扩展暂缓，优先完成小范围策略对齐。')
text=text.replace('全题结果将在扩展完成后更新。','当前优先进行固定小范围策略验证。')
(HERE/'subset_draft_zh.md').write_text(text,encoding='utf-8')
print('Built subset draft with traceable completed evidence; full-population delivery remains active.')
