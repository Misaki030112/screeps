<template>
  <figure class="plate">
    <p class="kicker">存储到隔壁的控制器</p>
    <div class="flow">
      <div class="node">
        <strong>家的存储 · W46N8</strong>
        <span>至少 20000 才开始搬。一次搬运留下不低于 18000。15000 的防御地板不动。</span>
      </div>
      <p class="arrow">↓</p>
      <div class="node now">
        <strong>家的搬运工 → 终端 35,31</strong>
        <span>补到 6000 为止。这一趟少于 400 不开。36,30 同时挨着存储和终端。</span>
      </div>
      <p class="arrow">↓</p>
      <div class="node">
        <strong>终端发出 5000</strong>
        <span>另扣手续费 164。每 5 拍才看一次。冷却中、或 W47 终端空位不足 15000，这一拍不发。</span>
      </div>
      <p class="arrow">↓</p>
      <div class="node now">
        <strong>W47 终端 · 33,32</strong>
        <span>留下 3000。高出至少 200 时，站在 34,32 的 filler 先从这里取。</span>
      </div>
      <p class="arrow">↓</p>
      <div class="flow-split">
        <div class="node done">
          <strong>枢纽还缺</strong>
          <span>先补出生点和延伸。送来的能量不必先绕进存储。</span>
        </div>
        <div class="node">
          <strong>枢纽已满</strong>
          <span>放进 W47 的存储 35,32。升级工的闩看的是这份存储。</span>
        </div>
        <div class="node stop">
          <strong>暂停</strong>
          <span>外矿还没有第一只防御身体、家有敌对 creep、或 W47 存储加终端已到 15 万。升级目标不因此回到 1。</span>
        </div>
      </div>
    </div>
    <figcaption>
      只在 W46N8 和 W47N8 两间自己的房间之间走。没有市场订单。W47 到了 8 级，整段关掉，家的升级目标回到 1。
    </figcaption>
  </figure>
</template>
