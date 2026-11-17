# CPU

账号在 shard3 上每 tick 20。源码不写死这个数，它读 `Game.cpu.tickLimit` 和 `Game.cpu.bucket`。

桶低于 2000（`src/utils/cpuorder.js`）时，守卫和远程防御先跑，然后是女王和 W47 的 filler，其余经济单位在距离本 tick 上限不足 5 时停一拍。停一拍是为了让防御和结尾的统计还能写完。

外矿防御的状态机在桶低于 3000 时不派兵。房间视觉在桶低于 2000 时不画。把桶维持在 5000 以上是操作习惯，不是代码里的闸。

主循环的顺序见手册 `docs-site/mechanisms/loop.md`。
