# 殖民地手册

Misaki 在 Screeps shard3 上的殖民地。家是 **W46N8**，第二间房是 **W47N8**，外矿是 **W45N8**、**W45N7** 和 **W47N7**。

给人读的说明在公开手册里：[殖民地手册](https://screeps-handbook-nolove-world.vercel.app)。源码在 [`docs-site/`](docs-site/)。手册从当前的 `src/` 写起：能量地板、孵化、搬运、升级、防御、实验室、矿物和部署。它不收录巡逻日志，也不包含令牌或内网地址。

## 仓库里有什么

- `src/` 是游戏代码。W47N8 走自己的房间模块，其余出生点走家的孵化。
- `docs-site/` 是手册网站。
- `docs/` 和根目录上的短文只保留仍然成立的要点，并指向手册。十二小时记录不再放在这里。
- `node scripts/check.js` 构建、做语法检查、跑模拟和单元测试。
- `node upload.js` 在检查通过之后上传。令牌只留在执行上传的那台机器上，不进仓库。

## 本地看手册

```bash
cd docs-site
npm ci
npm run dev
```
