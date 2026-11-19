<template>
  <figure class="plate">
    <p class="kicker">位置没变才计数，疲劳不算</p>
    <div class="arch-col ladder">
      <div class="step">
        <span class="num">2</span>
        <div class="node">
          <strong>绕一次</strong>
          <span>把 creep 当成障碍再搜。比剩下的旧路贵过 12，或没搜完，就留下旧路，这一拍不动。</span>
        </div>
      </div>
      <div class="step">
        <span class="num">4</span>
        <div class="node now">
          <strong>换位</strong>
          <span>下一格是自己的、不在固定站上、也没有疲劳，就请它朝反方向迈。一直到第 8 拍之前。</span>
        </div>
      </div>
      <div class="step">
        <span class="num">8</span>
        <div class="node">
          <strong>迈开</strong>
          <span>八个方向按这一拍轮一个。同时重算。这一拍不沿新路走。</span>
        </div>
      </div>
      <div class="step">
        <span class="num">30</span>
        <div class="node">
          <strong>一行</strong>
          <span>控制台打一行 STUCK，并重算。不回收。之后每 30 拍再重算，不再打那一行。</span>
        </div>
      </div>
    </div>
    <figcaption>
      窄路从第 2 拍就换位，第 2 拍不绕。
    </figcaption>
  </figure>
</template>
