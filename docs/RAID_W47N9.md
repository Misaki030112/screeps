# W47N9 进攻（破口 39,42 → 先拆塔 → 逼 SM）

Misaki 2026-10-29（t333）：**持续派波**直到 BustJetter 开 safe mode。编制含 **近战 + 远程 + 治疗**，两房（home W46N8 + colony W47N8）集中能量出兵；停非必要建造/升级分心。破口 **(39,42)** 墙/rampart，进房后 **先拆塔**，再打 creep、拆建筑，歼灭施压。

Code: `src/roles/raid9.js`，控制 `tools/raid9.py`，测试 `tests/raid9.js`。
**不自动开我方 SM。**

## 目标序（每 tick）

1. **破口屏障**：`rampart` / `constructedWall` 距 (39,42) ≤2  
2. **塔**  
3. **敌 creep**（武装优先）  
4. **其它非路建筑**（spawn 略优先）

不再以 spawn-first / 追 feeder 为主。

## 编制与持续派波

| 槽 | 体型 | 造价 | 数量 |
|---|---|---|---|
| melee | 2T 16A 18M | 2200 | 2 |
| ranged | 10RA 11M 1H | 2300 | 2 |
| heal | 7H 7M | 2100 | 2 |
| **合计 / 波** | | **~13200** | **6** |

- 出兵：**W46N8 与 W47N8 均可**（`wantSpawn` 两边）；存活不足 WAVE 且 `on` 且未 SM/garrison 时自动补员。  
- 集结：W47N8 北口偏东 `38–41,y=1–2`（近战前排、远程/治疗后排），齐 6 再进。  
- 进房：近战先，远程/治疗跟；治疗贴近战回血。  
- **一波死光不停止**；清空 `go` 后下一波再集结。SM / overrun / `abort` 才停。

`Memory.ops.w47n9` 标志：

| 字段 | 含义 |
|---|---|
| `on` | 造兵总开关 |
| `n` | 累计已造数量（统计） |
| `go` | 本波已齐员出发 tick |
| `safe` / `safeUntil` | 对方 SM → 撤回 garrison，不再造 |
| `flee` / `garrison` | overrun 或 `abort` |
| （隐式）`pauseCivilians` | `on && !safe && !garrison && !flee` 时 home/colony 停 builder、upgrader 压到 1 |

## 止损

| 条件 | 动作 |
|---|---|
| W47N9 safe mode | 烧 SM 成功；garrison；停造 |
| 房内敌 ATTACK+RA ≥12 | flee → garrison |
| `raid9.py abort` | 停造 + garrison |
| 单波阵亡 | **继续补下一波**（不因此 abort） |

## 启动

```bash
python3 tools/raid9.py status
python3 tools/raid9.py arm    # Memory.ops.w47n9={on:true,n:0}，清 safe/garrison/go/flee
python3 tools/raid9.py abort  # 紧急停
```

## 风险

- 破口东侧 ~84k rampart，需治疗续航；塔在 39,37 / 34,28，破口后先点塔。  
- 两房合计 ~13k/波，storage 可花（Misaki）。  
- 侧翼 W48N9 回防 → overrun 阈值。
