<template>
  <figure class="plate">
    <p class="kicker">一个 tick 里谁先说话</p>
    <div class="arch">
      <div class="arch-col">
        <div class="step"><span class="num">1</span><div class="node"><strong>忘掉死人</strong><span>Memory.creeps 里已经不在的名字删掉</span></div></div>
        <div class="step"><span class="num">2</span><div class="node"><strong>孵化</strong><span>W47N8 用自己的队列；别的出生点用家的</span></div></div>
        <div class="step"><span class="num">3</span><div class="node"><strong>房间</strong><span>布局和塔。家再跑 link、实验室、警报</span></div></div>
        <div class="step"><span class="num">4</span><div class="node"><strong>外矿与路</strong><span>威胁状态机，然后 RCL6 以上的道路</span></div></div>
      </div>
      <div class="arch-col">
        <div class="step"><span class="num">5</span><div class="node"><strong>指挥官，如果开着</strong><span>没设 Memory.cmd 时，这里只是一次判断</span></div></div>
        <div class="step"><span class="num">6</span><div class="node now"><strong>Creep</strong><span>桶够用就按原顺序。桶低于 2000，先打仗和补能</span></div></div>
        <div class="step"><span class="num">7</span><div class="node"><strong>快到本 tick 上限</strong><span>其余 creep 停一拍，把统计和报告留出来</span></div></div>
        <div class="step"><span class="num">8</span><div class="node done"><strong>STATS</strong><span>一行控制台摘要，给以后的人看，不驱动行为</span></div></div>
      </div>
    </div>
    <figcaption>主循环在 src/main.js。CPU 预算是账号的每 tick 20，代码读的是当场的 bucket 和 tickLimit。</figcaption>
  </figure>
</template>
