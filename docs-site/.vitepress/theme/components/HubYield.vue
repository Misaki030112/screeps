<template>
  <figure class="plate">
    <p class="kicker">W47N8 枢纽这一角 · x 向右，y 向下</p>
    <div class="hub">
      <div class="node stop c3231">
        <strong>32,31 延伸</strong>
        <span>口袋的北墙。</span>
      </div>
      <div class="node c3331">
        <strong>33,31 路</strong>
        <span>出口。被占时从这里离开。</span>
      </div>
      <div class="node c3232">
        <strong>32,32 平地</strong>
        <span>空着按 2。被占时这一次写成 8。</span>
      </div>
      <div class="node stop c3332">
        <strong>33,32 终端</strong>
        <span>挡住。</span>
      </div>
      <div class="node now c3432">
        <strong>34,32 岗位</strong>
        <span>路，代价 4。filler 仍走得进。</span>
      </div>
      <div class="node stop c3233">
        <strong>32,33 link</strong>
        <span>挡住。旁边的 32,32 仍开着。</span>
      </div>
      <div class="node c3333">
        <strong>33,33 容器</strong>
        <span>平时是路的 1。被占时这一次写成 8。</span>
      </div>
      <div class="node done c3433">
        <strong>34,33 路</strong>
        <span>被占时南下。仍是 1。</span>
      </div>
      <div class="node stop c3234">
        <strong>32,34 延伸</strong>
        <span>不在对角上。没有挪。</span>
      </div>
      <div class="node done c3334">
        <strong>33,34 路</strong>
        <span>南下接上。仍是 1。</span>
      </div>
    </div>
    <ul class="legend">
      <li><i class="lg-now"></i>岗位，代价 4</li>
      <li><i class="lg-done"></i>容器被占时的南下</li>
      <li><i class="lg-stop"></i>建筑，走不过</li>
    </ul>
    <figcaption>
      容器空着，过路走 32,32 再进 33,33。容器上有人，南下走 34,32 → 34,33 → 33,34。已经在 32,32，从 33,31 出来。
    </figcaption>
  </figure>
</template>
